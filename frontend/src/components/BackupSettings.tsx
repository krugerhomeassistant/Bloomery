import { useEffect, useRef, useState } from 'react'
import { format, parseISO } from 'date-fns'
import { CheckCircle2, Cloud, Download, HardDrive, RotateCcw, XCircle } from 'lucide-react'
import { api } from '../api'
import { Sheet } from './ui'

type File = { id?: string; name: string; size: number; created: string }
type Info = {
  enabled: boolean; time: string; tz: string; keep: number; last: string; last_ok: boolean | null; last_error: string
  encrypted: boolean; gdrive: { client_id: string; has_secret: boolean; connected: boolean }
  local: File[]; cloud: File[] | null; cloud_error: string
}
type Restore = { from: 'file'; file: Blob; name: string } | { from: 'cloud'; id: string; name: string } | { from: 'local'; name: string }

const kb = (n: number) => (n > 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`)
const when = (iso: string) => format(parseISO(iso), 'd MMM yyyy, HH:mm')

type Msg = { ok: boolean; text: string }

export default function BackupSettings({ open, onClose, notice }: { open: boolean; onClose: () => void; notice?: Msg | null }) {
  const [info, setInfo] = useState<Info | null>(null)
  const [f, setF] = useState({ enabled: true, time: '03:00', keep: 14, passphrase: '', clientId: '', clientSecret: '' })
  const [msg, setMsg] = useState<Msg | null>(notice ?? null)
  const [busy, setBusy] = useState('')
  const [restore, setRestore] = useState<Restore | null>(null)
  const [restorePass, setRestorePass] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  const redirectUri = `${location.origin}/api/backups/google/callback`

  const load = () =>
    api<Info>('/api/backups', { today: false }).then((i) => {
      setInfo(i)
      setF((x) => ({ ...x, enabled: i.enabled, time: i.time, keep: i.keep, clientId: i.gdrive.client_id }))
    })
  useEffect(() => {
    if (open) { setMsg(notice ?? null); setRestore(null); load().catch((e) => setMsg({ ok: false, text: e.message })) }
  }, [open])

  const act = async (label: string, fn: () => Promise<unknown>, done?: string) => {
    setBusy(label); setMsg(null)
    try {
      await fn()
      if (done) setMsg({ ok: true, text: done })
      await load()
    } catch (e: any) {
      setMsg({ ok: false, text: e.message })
    } finally {
      setBusy('')
    }
  }
  const save = (extra: Record<string, unknown> = {}) =>
    api('/api/backups/config', {
      method: 'PUT', today: false,
      body: { enabled: f.enabled, time: f.time, tz, keep: f.keep, gdrive_client_id: f.clientId, ...extra },
    })
  const runNow = () => act('run', async () => {
    const r = await api<{ name: string; cloud: boolean; error: string }>('/api/backups/run', { method: 'POST', today: false })
    if (r.error) throw new Error(`Saved on the server, but Google Drive failed: ${r.error}`)
  }, 'Backup made')
  const connect = () => act('google', async () => {
    await save(f.clientSecret ? { gdrive_client_secret: f.clientSecret } : {})
    const { url } = await api<{ url: string }>(`/api/backups/google/start?origin=${encodeURIComponent(location.origin)}`, { today: false })
    location.href = url
  })
  const doRestore = () => act('restore', async () => {
    if (!restore) return
    let r: Response
    const headers = { 'X-Backup-Passphrase': restorePass }
    if (restore.from === 'cloud') r = await fetch(`/api/backups/restore/cloud/${restore.id}`, { method: 'POST', headers })
    else {
      const blob = restore.from === 'file' ? restore.file : await (await fetch(`/api/backups/file/${restore.name}`)).blob()
      r = await fetch('/api/backups/restore', { method: 'POST', headers: { ...headers, 'Content-Type': 'application/octet-stream' }, body: blob })
    }
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText)
    location.reload()
  })

  if (!info) return <Sheet open={open} onClose={onClose} title="Backups"><p className="p-5 text-muted">{msg?.text ?? 'Loading…'}</p></Sheet>
  const encryptedName = (n: string) => n.endsWith('.enc')

  return (
    <Sheet open={open} onClose={onClose} title="Backups" full>
      <div className="space-y-5 px-5 pb-10">
        <div className={`flex items-start gap-3 rounded-2xl p-4 text-sm ${info.last_ok === false ? 'bg-pink-50' : 'bg-teal-50'}`}>
          {info.last_ok === false ? <XCircle className="shrink-0 text-pink-600" /> : <CheckCircle2 className="shrink-0 text-teal-600" />}
          <div>
            <div className="font-bold">{info.last ? `Last backup ${when(info.last)}` : 'No backups yet'}</div>
            {info.last_error && <div className="text-muted">{info.last_error}</div>}
            <div className="text-muted">{info.encrypted ? '🔒 Encrypted with your passphrase' : 'Not encrypted'} · {info.gdrive.connected ? 'Also saved to Google Drive' : 'Saved on your server only'}</div>
          </div>
        </div>

        <button className="btn-primary w-full" disabled={!!busy} onClick={runNow}>{busy === 'run' ? 'Backing up…' : 'Back up now'}</button>
        {msg && <p className={`text-sm font-bold ${msg.ok ? 'text-teal-600' : 'text-pink-600'}`}>{msg.text}</p>}

        <section className="card space-y-3 p-4">
          <label className="flex items-center justify-between font-semibold">
            Daily backup
            <input type="checkbox" className="h-5 w-5 accent-pink-500" checked={f.enabled} onChange={(e) => setF({ ...f, enabled: e.target.checked })} />
          </label>
          <label className="flex items-center justify-between text-sm">
            <span>At</span>
            <input type="time" className="input w-32 py-1.5" value={f.time} onChange={(e) => setF({ ...f, time: e.target.value })} />
          </label>
          <label className="flex items-center justify-between text-sm">
            <span>Keep the newest</span>
            <select className="input w-32 py-1.5" value={f.keep} onChange={(e) => setF({ ...f, keep: +e.target.value })}>
              {[7, 14, 30, 90].map((n) => <option key={n} value={n}>{n} backups</option>)}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-semibold">Encryption passphrase</span>
            <input className="input" type="password" autoComplete="new-password" value={f.passphrase}
              placeholder={info.encrypted ? '•••••••• (set; type to change)' : 'Optional, at least 8 characters'}
              onChange={(e) => setF({ ...f, passphrase: e.target.value })} />
            <span className="mt-1 block text-xs text-muted">Recommended for cloud backups. Write it down: without it an encrypted backup can't be restored.</span>
          </label>
          <div className="flex flex-wrap gap-2">
            <button className="btn-primary px-4 py-2 text-sm" disabled={!!busy}
              onClick={() => act('save', () => save(f.passphrase ? { passphrase: f.passphrase } : {}).then(() => setF((x) => ({ ...x, passphrase: '' }))), 'Saved')}>Save</button>
            {info.encrypted && <button className="btn-ghost px-4 py-2 text-sm" disabled={!!busy}
              onClick={() => act('save', () => save({ passphrase: '' }), 'Encryption turned off for new backups')}>Turn off encryption</button>}
          </div>
          <p className="text-xs text-muted">Time zone: {tz}</p>
        </section>

        <section className="card space-y-3 p-4">
          <h3 className="flex items-center gap-2 font-extrabold"><Cloud size={18} className="text-pink-500" /> Google Drive</h3>
          {info.gdrive.connected ? (
            <>
              <p className="text-sm text-muted">Connected. Each backup is also uploaded to the <b>Bloomery backups</b> folder in your Drive. Bloomery can only see files it created.</p>
              {info.cloud_error && <p className="text-sm font-bold text-pink-600">{info.cloud_error}</p>}
              <FileList files={info.cloud ?? []} icon={<Cloud size={16} />} onRestore={(x) => setRestore({ from: 'cloud', id: x.id!, name: x.name })} />
              <button className="btn-ghost px-4 py-2 text-sm" disabled={!!busy}
                onClick={() => act('google', () => api('/api/backups/google', { method: 'DELETE', today: false }), 'Google Drive disconnected')}>Disconnect</button>
            </>
          ) : (
            <>
              <details className="rounded-2xl bg-pink-50 p-3 text-xs text-muted" open={!info.gdrive.client_id}>
                <summary className="cursor-pointer font-bold text-ink">One-time setup (about 5 minutes)</summary>
                <ol className="mt-2 list-decimal space-y-1.5 pl-4">
                  <li>Open <a className="font-bold text-pink-600" href="https://console.cloud.google.com/projectcreate" target="_blank" rel="noreferrer">Google Cloud Console</a> and create a project (any name).</li>
                  <li>Enable the <a className="font-bold text-pink-600" href="https://console.cloud.google.com/apis/library/drive.googleapis.com" target="_blank" rel="noreferrer">Google Drive API</a>.</li>
                  <li><b>Google Auth Platform → Branding</b>: app name "Bloomery", your email. <b>Audience</b>: External, then <b>Publish app</b> (otherwise Google disconnects it after 7 days; no review is needed for this permission).</li>
                  <li><b>Clients → Create client</b>: type <i>Web application</i>, authorised redirect URI:
                    <code className="mt-1 block select-all break-all rounded bg-card p-2 text-ink">{redirectUri}</code></li>
                  <li>Paste the client ID and secret below and tap <b>Connect</b>.</li>
                </ol>
              </details>
              <input className="input" placeholder="Client ID (…apps.googleusercontent.com)" value={f.clientId} onChange={(e) => setF({ ...f, clientId: e.target.value })} />
              <input className="input" type="password" autoComplete="off" placeholder={info.gdrive.has_secret ? 'Client secret (saved)' : 'Client secret'}
                value={f.clientSecret} onChange={(e) => setF({ ...f, clientSecret: e.target.value })} />
              <button className="btn-primary w-full" disabled={!!busy || !f.clientId || !(f.clientSecret || info.gdrive.has_secret)} onClick={connect}>
                {busy === 'google' ? 'Opening Google…' : 'Connect Google Drive'}</button>
              {!location.origin.startsWith('https://') && <p className="text-xs font-bold text-pink-600">Google needs Bloomery to be opened over HTTPS.</p>}
            </>
          )}
        </section>

        <section className="card space-y-3 p-4">
          <h3 className="flex items-center gap-2 font-extrabold"><HardDrive size={18} className="text-pink-500" /> On this server</h3>
          <FileList files={info.local} icon={<HardDrive size={16} />} download onRestore={(x) => setRestore({ from: 'local', name: x.name })} />
          <button className="btn-ghost w-full text-sm" onClick={() => fileInput.current?.click()}>Restore from a file…</button>
          <input ref={fileInput} type="file" hidden onChange={(e) => {
            const file = e.target.files?.[0]; e.target.value = ''
            if (file) setRestore({ from: 'file', file, name: file.name })
          }} />
        </section>
      </div>

      <Sheet open={!!restore} onClose={() => setRestore(null)} title="Restore this backup?">
        {restore && (
          <div className="space-y-3 px-5 pb-8">
            <p className="text-sm"><b>{restore.name}</b> replaces <b>all</b> current data for every account on this server. A safety copy of today's data is saved first.</p>
            {(restore.from === 'file' || encryptedName(restore.name)) && (
              <input className="input" type="password" placeholder={encryptedName(restore.name) ? 'Backup passphrase' : 'Passphrase (if encrypted)'}
                value={restorePass} onChange={(e) => setRestorePass(e.target.value)} />
            )}
            {msg && !msg.ok && <p className="text-sm font-bold text-pink-600">{msg.text}</p>}
            <button className="btn w-full bg-pink-600 text-white" disabled={!!busy} onClick={doRestore}>
              {busy === 'restore' ? 'Restoring…' : 'Restore'}</button>
          </div>
        )}
      </Sheet>
    </Sheet>
  )
}

function FileList({ files, icon, download, onRestore }: { files: File[]; icon: React.ReactNode; download?: boolean; onRestore: (f: File) => void }) {
  if (!files.length) return <p className="text-sm text-muted">No backups here yet.</p>
  return (
    <ul className="divide-y divide-line text-sm">
      {files.slice(0, 10).map((x) => (
        <li key={x.id ?? x.name} className="flex items-center gap-2 py-2">
          <span className="text-muted">{icon}</span>
          <span className="flex-1">{when(x.created)}<span className="block text-xs text-muted">{kb(x.size)}{x.name.endsWith('.enc') ? ' · 🔒' : ''}{x.name.includes('prerestore') ? ' · safety copy' : ''}</span></span>
          {download && <a className="rounded-full p-2 text-muted hover:bg-pink-100" href={`/api/backups/file/${x.name}`} download aria-label="Download"><Download size={18} /></a>}
          <button className="rounded-full p-2 text-muted hover:bg-pink-100" onClick={() => onRestore(x)} aria-label="Restore"><RotateCcw size={18} /></button>
        </li>
      ))}
    </ul>
  )
}
