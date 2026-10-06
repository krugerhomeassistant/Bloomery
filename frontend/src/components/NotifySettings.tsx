import { useEffect, useState } from 'react'
import { CheckCircle2, Smartphone, XCircle } from 'lucide-react'
import { api } from '../api'
import { Sheet } from './ui'
import { currentPushSubscription, disablePush, enablePush, needsHomeScreen, pushSupported } from '../webauthn'

type Cfg = { url: string; time: string; tz: string; kinds: string[] }
const KINDS: [string, string, string][] = [
  ['milestone', '🌺', 'Milestones: period started, fertile window, period due or late'],
  ['forecast', '🔮', 'Heads-ups: symptoms you usually get around this day'],
  ['recap', '📊', 'Cycle recap when a new cycle starts'],
  ['tip', '💡', 'A daily tip for your cycle phase'],
  ['pill', '💊', 'Birth control reminders: pill, ring, patch, injection, IUD checks (set your method in Profile)'],
]

export default function NotifySettings({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [f, setF] = useState<Cfg | null>(null)
  const [res, setRes] = useState<{ ok: boolean; msg: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone

  const [device, setDevice] = useState(false)
  useEffect(() => {
    if (open) {
      setRes(null)
      api<Cfg>('/api/notifications', { today: false }).then(setF)
      currentPushSubscription().then((s) => setDevice(!!s)).catch(() => setDevice(false))
    }
  }, [open])
  const toggleDevice = async () => {
    setBusy(true); setRes(null)
    try {
      if (device) { await disablePush(); setDevice(false) }
      else { await enablePush(); setDevice(true); await api('/api/notifications', { method: 'PUT', body: { ...f, tz }, today: false }) }
    } catch (e: any) {
      setRes({ ok: false, msg: e.message })
    } finally {
      setBusy(false)
    }
  }
  if (!f) return <Sheet open={open} onClose={onClose} title="Notifications"><p className="p-5 text-muted">Loading…</p></Sheet>

  const toggle = (k: string) => setF({ ...f, kinds: f.kinds.includes(k) ? f.kinds.filter((x) => x !== k) : [...f.kinds, k] })
  const run = async (kind: 'test' | 'save') => {
    setBusy(true)
    setRes(null)
    const body = { ...f, tz }
    try {
      if (kind === 'test') {
        const r = await api<{ ok: boolean; title?: string; error?: string }>('/api/notifications/test', { body })
        setRes({ ok: r.ok, msg: r.ok ? `Sent "${r.title}". Check your ${device && !f.url ? 'device' : 'phone'}.` : r.error! })
      } else {
        await api('/api/notifications', { method: 'PUT', body, today: false })
        onClose()
      }
    } catch (e: any) {
      setRes({ ok: false, msg: e.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Sheet open={open} onClose={onClose} title="Notifications">
      <div className="space-y-4 px-5 pb-8">
        <div className="card flex items-center gap-3 p-4">
          <Smartphone className="shrink-0 text-pink-500" />
          <div className="flex-1">
            <div className="font-bold">This device</div>
            <div className="text-xs text-muted">{!pushSupported()
              ? (needsHomeScreen() ? 'Add Bloomery to your Home Screen (Share → Add to Home Screen), open it from there, then turn this on.' : 'Needs Bloomery to be opened over HTTPS in a browser that supports notifications.')
              : device ? 'Notifications are sent straight to this device.' : 'Get notifications on this phone or computer, no extra app needed.'}</div>
          </div>
          <input type="checkbox" className="h-5 w-5 accent-pink-500" disabled={busy || !pushSupported()} checked={device} onChange={toggleDevice} aria-label="Notifications on this device" />
        </div>

        <label className="block">
          <span className="mb-1 block text-sm font-bold text-muted">Or send to a URL (ntfy, Gotify, Home Assistant, Discord)</span>
          <input className="input" value={f.url} placeholder="https://ntfy.sh/your-secret-topic" inputMode="url"
            onChange={(e) => setF({ ...f, url: e.target.value })} />
        </label>
        <details className="rounded-2xl bg-pink-50 p-3 text-xs text-muted">
          <summary className="cursor-pointer font-bold text-ink">Which URL do I use?</summary>
          <ul className="mt-2 list-disc space-y-1.5 pl-4">
            <li><b>ntfy</b> (easiest): install the ntfy app, subscribe to a hard-to-guess topic, paste <code>https://ntfy.sh/that-topic</code> (or your own ntfy server).</li>
            <li><b>Gotify:</b> <code>https://gotify.your.lan/message?token=APP_TOKEN</code></li>
            <li><b>Home Assistant:</b> <code>http://ha.local:8123/api/webhook/your-id</code>. Fields <code>title</code> and <code>message</code> arrive in <code>trigger.json</code>.</li>
            <li><b>Discord:</b> a channel webhook URL.</li>
          </ul>
          <p className="mt-2">Notifications only contain short cycle messages, never your logs. With public ntfy.sh, pick a topic nobody could guess.</p>
        </details>

        <label className="flex items-center justify-between">
          <span className="font-semibold">Send at</span>
          <input type="time" className="input w-36 py-2" value={f.time} onChange={(e) => setF({ ...f, time: e.target.value })} />
        </label>
        <p className="-mt-2 text-xs text-muted">Your time zone: {tz}</p>

        <div className="card divide-y divide-line">
          {KINDS.map(([k, emoji, label]) => (
            <label key={k} className="flex cursor-pointer items-center gap-3 px-4 py-3 text-sm">
              <span className="text-lg">{emoji}</span><span className="flex-1">{label}</span>
              <input type="checkbox" className="h-5 w-5 accent-pink-500" checked={f.kinds.includes(k)} onChange={() => toggle(k)} />
            </label>
          ))}
        </div>
        <p className="text-xs text-muted">At most one message a day, combining whatever is relevant. Nothing is sent on quiet days.</p>

        {res && (
          <div className={`flex gap-2 rounded-2xl p-3 text-sm ${res.ok ? 'bg-teal-50 text-teal-600' : 'bg-pink-50 text-pink-600'}`}>
            {res.ok ? <CheckCircle2 size={18} className="shrink-0" /> : <XCircle size={18} className="shrink-0" />}
            <span className="break-words">{res.msg}</span>
          </div>
        )}
        <div className="flex gap-3">
          <button className="btn-ghost flex-1" disabled={busy || !(f.url || device)} onClick={() => run('test')}>Send test</button>
          <button className="btn-primary flex-1" disabled={busy} onClick={() => run('save')}>Save</button>
        </div>
      </div>
    </Sheet>
  )
}
