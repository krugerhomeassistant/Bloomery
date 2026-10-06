import { useRef, useState, type ReactNode } from 'react'
import { Type, Languages, Bell, ChevronRight, Download, LogOut, Moon, Sparkles, Trash2, Upload, KeyRound, Lock, DatabaseBackup, Pill } from 'lucide-react'
import { api, iso, type LifeStage, type Overview, type User } from '../api'
import { LOCK_CHOICES, lockAfterMin, setLockAfter, useApp, useFetch } from '../state'
import { SectionTitle, Sheet, Stepper } from '../components/ui'
import { extractAppleHealth } from '../appleHealth'
import AiSettings from '../components/AiSettings'
import NotifySettings from '../components/NotifySettings'
import BackupSettings from '../components/BackupSettings'
import Passkeys from '../components/Passkeys'
import Automations from '../components/Automations'
import Words from '../components/Words'
import BirthControl, { METHODS } from '../components/BirthControl'
import { LANGS, N_, t, type Lang } from '../i18n'

const STAGE_HELP: Record<LifeStage, string> = {
  cycle: N_('Period and fertility predictions from your logs.'),
  pregnancy: N_('Shows your pregnancy week, due date and weekly tips instead of period predictions. Your cycle history is kept.'),
  perimenopause: N_('Expects irregular cycles: wider prediction ranges, days since your last period and the 12-month menopause marker.'),
}

export default function Profile() {
  const { user, setUser, bump, theme, setTheme, lang, changeLang } = useApp()
  const ov = useFetch<Overview>('/api/cycle/overview').data
  const share = useFetch<{ token: string | null }>('/api/tokens/share')
  const ha = useFetch<{ token: string | null }>('/api/tokens/ha')
  const [copied, setCopied] = useState(false)
  const health = useFetch<{ version: string }>('/api/health').data
  const ai = useFetch<{ enabled: boolean; provider: string; model: string | null; local: boolean }>('/api/ai/status').data
  const [editing, setEditing] = useState<null | 'cycle_length' | 'period_length' | 'luteal_length'>(null)
  const [val, setVal] = useState(0)
  const [pw, setPw] = useState<null | { current: string; new: string; msg?: string }>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [after, setAfter] = useState(lockAfterMin)
  const [lock, setLock] = useState<null | { pin: string; password: string; msg?: string }>(null)
  const [msg, setMsg] = useState('')
  const [aiOpen, setAiOpen] = useState(false)
  const [notifyOpen, setNotifyOpen] = useState(false)
  const [bcOpen, setBcOpen] = useState(false)
  const [wordsOpen, setWordsOpen] = useState(false)
  const bc = useFetch<{ config: { method: string } }>('/api/contraception', [bcOpen]).data
  const bcLabel = t(METHODS.find(([v]) => v === (bc?.config.method ?? 'none'))?.[1] ?? '').replace(/ \/ (not tracking|nie gevolg nie)/, '')
  // back from Google sign-in: /profile?backup=google-connected|google-failed opens the sheet with the result
  const [backupReturn] = useState(() => {
    const b = new URLSearchParams(location.search).get('backup')
    if (b) history.replaceState(null, '', location.pathname)
    return b
  })
  const [backupOpen, setBackupOpen] = useState(!!backupReturn)
  const file = useRef<HTMLInputElement>(null)
  if (!user) return null

  const setStage = async (mode: LifeStage, lmp: string | null) => {
    setUser(await api<User>('/api/life-stage', { method: 'PUT', body: { mode, lmp }, today: false }))
    bump()
  }
  const save = async (patch: Partial<User>) => {
    setUser(await api<User>('/api/profile', { method: 'PUT', body: patch, today: false }))
    bump()
  }
  const exportData = async () => {
    const data = await api('/api/export', { today: false })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
    a.download = `bloomery-export-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
  }
  const importData = async (f: File) => {
    try {
      if (/\.zip$/i.test(f.name)) throw new Error(t('Unzip the Apple Health export first, then pick apple_health_export/export.xml'))
      if (/\.xml$/i.test(f.name)) {
        setMsg(t('Reading Apple Health export… {p}%', { p: 0 }))
        const data = await extractAppleHealth(f, (p) => setMsg(t('Reading Apple Health export… {p}%', { p })))
        if (!data.records.length) throw new Error(t('No cycle data (menstruation, symptoms, temperature) found in this export'))
        const r = await api<{ days: number; period_days: number; first: string; last: string }>('/api/import/other', { body: { content: JSON.stringify(data) }, today: false })
        setMsg(t('Imported {days} days from Apple Health ({period_days} period days, {first} → {last})', r))
        bump()
        return
      }
      const text = await f.text()
      let j: any = null
      try { j = JSON.parse(text) } catch {}
      if (j?.app === 'bloomery') {
        const r = await api<{ imported: number }>('/api/import', { body: { logs: j.logs ?? [], replace: false }, today: false })
        setMsg(t('Imported {n} days', { n: r.imported }))
      } else {
        const r = await api<{ source: string; days: number; first: string; last: string }>('/api/import/other', { body: { content: text }, today: false })
        setMsg(t('Imported {days} period days from {source} ({first} → {last})', r))
      }
      bump()
    } catch (e: any) {
      setMsg(t('Import failed: {error}', { error: e.message }))
    }
  }
  const logout = async () => {
    await api('/api/auth/logout', { body: {}, today: false })
    setUser(null)
  }
  const LEARNED = { cycle_length: (o: any) => o.predicted_cycle_length, period_length: (o: any) => o.predicted_period_length, luteal_length: (o: any) => o.luteal_length }
  const shareUrl = share.data?.token ? `${location.origin}/share/${share.data.token}` : ''
  const tokenAct = async (kind: 'share' | 'ha', method: 'POST' | 'DELETE') => { (kind === 'share' ? share : ha).setData(await api<{ token: string | null }>(`/api/tokens/${kind}`, { method, body: method === 'POST' ? {} : undefined, today: false })); setCopied(false) }
  const shareAct = (m: 'POST' | 'DELETE') => tokenAct('share', m)
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  const haUrl = ha.data?.token ? `${location.origin}/api/ha/${ha.data.token}` : ''
  const LABEL = { cycle_length: N_('Cycle length'), period_length: N_('Period length'), luteal_length: N_('Luteal phase length') }
  const RANGE = { cycle_length: [15, 90], period_length: [1, 15], luteal_length: [8, 20] } as const

  return (
    <div className="px-4 pt-4 pb-10">
      <div className="card flex items-center gap-4 p-5">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-gradient-to-br from-pink-300 to-pink-500 text-2xl font-black text-white">
          {(user.display_name || user.username)[0]?.toUpperCase()}
        </div>
        <div>
          <div className="text-xl font-black">{user.display_name}</div>
          <div className="text-sm text-muted">@{user.username}</div>
        </div>
      </div>

      <SectionTitle>{t('Life stage')}</SectionTitle>
      <Group>
        <div className="px-4 py-3">
          <Segmented value={user.mode} onChange={(v) => setStage(v as LifeStage, v === 'pregnancy' ? user.lmp : null)}
            options={[['cycle', t('Cycle')], ['pregnancy', t('Pregnancy')], ['perimenopause', t('Perimenopause')]]} />
          {user.mode === 'pregnancy' && (
            <label className="mt-3 flex items-center justify-between gap-3 text-sm font-bold text-muted">{t('First day of last period')}
              <input type="date" className="input w-auto py-1.5" value={user.lmp ?? ov?.pregnancy?.lmp ?? ''} max={iso(new Date())}
                onChange={(e) => e.target.value && setStage('pregnancy', e.target.value)} />
            </label>
          )}
        </div>
      </Group>
      <p className="mt-2 px-2 text-xs text-muted">{t(STAGE_HELP[user.mode])}</p>

      <SectionTitle>{t('Cycle settings')}</SectionTitle>
      <Group>
        {(['cycle_length', 'period_length', 'luteal_length'] as const).map((k) => (
          <Row key={k} label={t(LABEL[k])} onClick={() => { setVal(user[k]); setEditing(k) }}
            value={t('{n} days', { n: user[k] }) + (ov && LEARNED[k](ov) !== user[k] ? ` · ${t('using {n}', { n: LEARNED[k](ov) })}` : '')} />
        ))}
        <Row icon={<Pill size={18} className="text-pink-500" />} label={t('Birth control')} value={bcLabel} onClick={() => setBcOpen(true)} />
        <div className="px-4 py-3">
          <div className="mb-2 text-sm font-bold text-muted">{t('Goal')}</div>
          <Segmented value={user.goal} onChange={(v) => save({ goal: v as User['goal'] })}
            options={[['track', t('Track cycle')], ['conceive', t('Get pregnant')], ['avoid', t('Understand fertility')]]} />
        </div>
      </Group>
      <p className="mt-2 px-2 text-xs text-muted">{t('These are your starting defaults. Once you\'ve logged enough cycles, Bloomery uses what it learned from your history ("using …").')}</p>

      <SectionTitle>{t('Preferences')}</SectionTitle>
      <Group>
        <div className="space-y-3 px-4 py-3">
          <div className="flex items-center justify-between"><span className="font-semibold">{t('Temperature')}</span>
            <Segmented value={user.temp_unit} onChange={(v) => save({ temp_unit: v as 'C' | 'F' })} options={[['C', '°C'], ['F', '°F']]} /></div>
          <div className="flex items-center justify-between"><span className="font-semibold">{t('Weight')}</span>
            <Segmented value={user.weight_unit} onChange={(v) => save({ weight_unit: v as 'kg' | 'lb' })} options={[['kg', 'kg'], ['lb', 'lb']]} /></div>
          <div className="flex items-center justify-between"><span className="flex items-center gap-2 font-semibold"><Moon size={18} /> {t('Theme')}</span>
            <Segmented value={theme} onChange={(v) => setTheme(v as any)} options={[['system', t('Auto')], ['light', t('Light')], ['dark', t('Dark')]]} /></div>
          <button className="flex w-full items-center justify-between text-left" onClick={() => setWordsOpen(true)}><span className="flex items-center gap-2 font-semibold"><Type size={18} /> {t('My words')}</span><span className="flex items-center gap-1 text-sm text-muted">{user.words.length || ''}<ChevronRight size={18} /></span></button>
          <div className="flex items-center justify-between"><span className="flex items-center gap-2 font-semibold"><Languages size={18} /> {t('Language')}</span>
            <Segmented value={lang} onChange={(v) => changeLang(v as Lang)} options={Object.entries(LANGS) as [string, string][]} /></div>
        </div>
      </Group>

      <SectionTitle>{t('AI assistant')}</SectionTitle>
      <Group>
        <button onClick={() => setAiOpen(true)} className="flex w-full items-center gap-3 px-4 py-4 text-left hover:bg-pink-50">
          <Sparkles className="shrink-0 text-[#7C5CE0]" />
          <div className="flex-1 text-sm">
            {ai?.enabled ? <><b>{t('On')}</b> · {ai.provider} · {ai.model}<div className="text-muted">{ai.local ? t('Runs on your server — data never leaves it.') : t('Cycle summaries are sent to this cloud provider.')}</div></>
              : <><b>{t('Off')}</b><div className="text-muted">{t('Tap to connect Claude, OpenAI or another provider.')}</div></>}
          </div>
          <ChevronRight size={18} className="text-muted" />
        </button>
      </Group>
      <AiSettings open={aiOpen} onClose={() => setAiOpen(false)} />

      <SectionTitle>{t('Notifications')}</SectionTitle>
      <Group>
        <Row icon={<Bell size={18} className="text-pink-500" />} label={t('Daily reminders & heads-ups')} onClick={() => setNotifyOpen(true)} />
      </Group>
      <NotifySettings open={notifyOpen} onClose={() => setNotifyOpen(false)} />
      <Words open={wordsOpen} onClose={() => setWordsOpen(false)} />
      <BirthControl open={bcOpen} onClose={() => setBcOpen(false)} />

      {user.is_owner && (
        <>
          <SectionTitle>{t('Backups')}</SectionTitle>
          <Group>
            <Row icon={<DatabaseBackup size={18} className="text-pink-500" />} label={t('Backups & restore')} value={t('Server + Google Drive')} onClick={() => setBackupOpen(true)} />
          </Group>
          <BackupSettings open={backupOpen} onClose={() => setBackupOpen(false)} notice={!backupReturn ? null :
            (backupReturn === 'google-connected' ? { ok: true, text: t('Google Drive connected. Backups are now uploaded there too.') }
              : { ok: false, text: t("Couldn't connect Google Drive. Check the client ID, secret and redirect URI, then try again.") })} />
        </>
      )}

      <SectionTitle>{t('Partner sharing')}</SectionTitle>
      <Group>
        <div className="space-y-3 px-4 py-4 text-sm">
          <p className="text-muted">{t('A private, read-only link showing where you are in your cycle, your predicted period and fertile days, plus tips for your partner. Symptoms, moods, sex and notes are never shared.')}</p>
          {shareUrl ? (
            <>
              <div className="select-all break-all rounded-2xl bg-pink-50 p-3 font-mono text-xs">{shareUrl}</div>
              <div className="flex flex-wrap gap-2">
                {window.isSecureContext && navigator.clipboard && (
                  <button className="btn-primary px-4 py-2 text-sm" onClick={() => navigator.clipboard.writeText(shareUrl).then(() => setCopied(true))}>{copied ? t('Copied!') : t('Copy link')}</button>
                )}
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => shareAct('POST')}>{t('New link')}</button>
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => shareAct('DELETE')}>{t('Stop sharing')}</button>
              </div>
            </>
          ) : (
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => shareAct('POST')}>{t('Create share link')}</button>
          )}
        </div>
      </Group>

      <SectionTitle>{t('Home Assistant & calendar')}</SectionTitle>
      <Group>
        <div className="space-y-3 px-4 py-4 text-sm">
          <p className="text-muted">{t('Private read-only feeds for Home Assistant sensors and your calendar app. Cycle dates only, never symptoms or notes.')}</p>
          {haUrl ? (
            <>
              <div className="font-bold">{t('1. Home Assistant sensors')}</div>
              <ol className="list-decimal space-y-1 pl-5 text-muted">
                <li>{t('HACS → ⋮ →')} <i>{t('Custom repositories')}</i> {t('→ add')} <code className="select-all break-all">{t('github.com/krugerhomeassistant/Bloomery')}</code> {t('as')} <i>{t('Integration')}</i>{t(', then download')} <b>{t('Bloomery')}</b> {t('and restart HA.')}</li>
                <li>{t('Settings → Devices & services →')} <i>{t('Add integration')}</i> → <b>{t('Bloomery')}</b> {t('→ paste:')}</li>
              </ol>
              <div className="select-all break-all rounded-2xl bg-pink-50 p-3 font-mono text-xs">{haUrl}</div>
              <p className="text-muted">{t('You get sensors plus')} <b>{t('Periods')}</b>, <b>{t('Fertile windows')}</b> {t('and')} <b>{t('Ovulation')}</b> {t('calendars, each with its own colour.')} <a className="font-bold text-pink-600" href="https://github.com/krugerhomeassistant/Bloomery/blob/main/docs/home-assistant.md" target="_blank" rel="noreferrer">{t('Full guide')}</a></p>
              <div className="font-bold">{t('2. Other calendar apps')}</div>
              <p className="text-muted">{t('Subscribe in Google, Apple or Outlook. Add one link per type if you want separate colours:')}</p>
              {([[N_('All events'), ''], [N_('Periods'), '&type=period'], [N_('Fertile windows'), '&type=fertile'], [N_('Ovulation'), '&type=ovulation']] as const).map(([label, q]) => (
                <div key={label}><div className="mb-1 text-xs font-bold text-muted">{t(label)}</div>
                  <div className="select-all break-all rounded-2xl bg-pink-50 p-3 font-mono text-xs">{haUrl}/calendar.ics?tz={tz}{q}</div></div>
              ))}
              <p className="text-xs text-muted">{t('The server must be reachable at this address from Home Assistant / your calendar app.')} <b>{t('New token')}</b> {t('disables the old links; Home Assistant will ask for the new one.')}</p>
              <div className="flex flex-wrap gap-2">
                {window.isSecureContext && navigator.clipboard && (
                  <button className="btn-primary px-4 py-2 text-sm" onClick={() => navigator.clipboard.writeText(haUrl).then(() => setCopied(true))}>{copied ? t('Copied!') : t('Copy integration URL')}</button>
                )}
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => tokenAct('ha', 'POST')}>{t('New token')}</button>
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => tokenAct('ha', 'DELETE')}>{t('Turn off')}</button>
              </div>
            </>
          ) : (
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => tokenAct('ha', 'POST')}>{t('Create feed')}</button>
          )}
        </div>
      </Group>

      <SectionTitle>{t('Shortcuts & automations')}</SectionTitle>
      <Group><Automations /></Group>

      <SectionTitle>{t('Your data')}</SectionTitle>
      <Group>
        <Row icon={<Download size={18} />} label={t('Export data (JSON)')} onClick={exportData} />
        <Row icon={<Upload size={18} />} label={t('Import data (Flo, Clue, Apple Health, CSV)')} onClick={() => file.current?.click()} />
        <Row icon={<Lock size={18} />} label={t('App lock (PIN)')} value={user.pin_set ? t('On') : t('Off')} onClick={() => setLock({ pin: '', password: '' })} />
        <Row icon={<KeyRound size={18} />} label={t('Change password')} onClick={() => setPw({ current: '', new: '' })} />
        <Row icon={<LogOut size={18} />} label={t('Log out')} onClick={logout} />
        <Row icon={<Trash2 size={18} />} label={t('Delete account & all data')} danger onClick={() => setConfirmDelete(true)} />
      </Group>
      <input ref={file} type="file" accept=".json,.csv,.cluedata,.xml,.zip,application/json,text/csv,text/xml" hidden onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) importData(f) }} />
      {msg && <p className="mt-3 text-center text-sm font-bold text-pink-600">{msg}</p>}
      <p className="mt-8 text-center text-xs text-muted">{t('Bloomery')} {health?.version && `v${health.version} `}{t('· self-hosted · your data stays yours')}</p>

      <Sheet open={!!editing} onClose={() => setEditing(null)} title={editing ? t(LABEL[editing]) : ''}>
        {editing && (
          <div className="px-5 pb-8 pt-4">
            <Stepper value={val} onChange={setVal} min={RANGE[editing][0]} max={RANGE[editing][1]} unit={t('days')} />
            <button className="btn-primary mt-8 w-full" onClick={async () => { await save({ [editing]: val }); setEditing(null) }}>{t('Save')}</button>
          </div>
        )}
      </Sheet>

      <Sheet open={!!lock} onClose={() => setLock(null)} title={t('App lock')}>
        {lock && (
          <form className="space-y-3 px-5 pb-8" onSubmit={async (e) => {
            e.preventDefault()
            const remove = (e.nativeEvent as SubmitEvent).submitter?.getAttribute('value') === 'remove'
            try {
              setUser(await api<User>('/api/auth/pin', { method: 'PUT', body: { password: lock.password, pin: remove ? null : lock.pin }, today: false }))
              setLock(null); setMsg(remove ? t('App lock turned off') : t('PIN saved'))
            } catch (err: any) { setLock({ ...lock, msg: err.message }) }
          }}>
            <p className="text-sm text-muted">{t('Asks for a 4-digit PIN when you come back to Bloomery after being away for a while. 10 wrong tries sign you out.')}</p>
            <input className="input text-center text-2xl tracking-[.5em]" type="password" inputMode="numeric" pattern="\d{4}" maxLength={4} autoComplete="off"
              placeholder="••••" value={lock.pin} onChange={(e) => setLock({ ...lock, pin: e.target.value.replace(/\D/g, '') })} required={!user.pin_set} />
            <input className="input" type="password" placeholder={t('Account password')} autoComplete="current-password" value={lock.password} onChange={(e) => setLock({ ...lock, password: e.target.value })} required />
            {lock.msg && <p className="text-sm font-bold text-pink-600">{lock.msg}</p>}
            <label className="flex items-center justify-between gap-3 text-sm font-bold text-muted">{t('Ask for PIN after')}
              <select className="input w-auto py-1.5" value={after} onChange={(e) => { setLockAfter(+e.target.value); setAfter(+e.target.value) }}>
                {LOCK_CHOICES.map(([m, l]) => <option key={m} value={m}>{t(l)} {t('away')}</option>)}
              </select>
            </label>
            <button className="btn-primary w-full" disabled={lock.pin.length !== 4}>{user.pin_set ? t('Change PIN') : t('Set PIN')}</button>
            {user.pin_set && <button value="remove" formNoValidate className="btn-ghost w-full">{t('Turn off app lock')}</button>}
          </form>
        )}
        {lock && user.pin_set && <div className="px-5 pb-8"><Passkeys /></div>}
      </Sheet>

      <Sheet open={!!pw} onClose={() => setPw(null)} title={t('Change password')}>
        {pw && (
          <form className="space-y-3 px-5 pb-8" onSubmit={async (e) => {
            e.preventDefault()
            try { await api('/api/auth/password', { body: { current: pw.current, new: pw.new }, today: false }); setPw(null); setMsg(t('Password changed')) }
            catch (err: any) { setPw({ ...pw, msg: err.message }) }
          }}>
            <input className="input" type="password" placeholder={t('Current password')} value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} />
            <input className="input" type="password" placeholder={t('New password (min 8)')} minLength={8} value={pw.new} onChange={(e) => setPw({ ...pw, new: e.target.value })} />
            {pw.msg && <p className="text-sm font-bold text-pink-600">{pw.msg}</p>}
            <button className="btn-primary w-full">{t('Update')}</button>
          </form>
        )}
      </Sheet>

      <Sheet open={confirmDelete} onClose={() => setConfirmDelete(false)} title={t('Delete everything?')}>
        <div className="space-y-3 px-5 pb-8">
          <p className="text-muted">{t('This permanently deletes your account, all logs and chat history from this server. Export first if you want a backup.')}</p>
          <button className="btn w-full bg-pink-600 text-white" onClick={async () => { await api('/api/account', { method: 'DELETE', today: false }); setUser(null) }}>{t('Delete permanently')}</button>
          <button className="btn-ghost w-full" onClick={() => setConfirmDelete(false)}>{t('Cancel')}</button>
        </div>
      </Sheet>
    </div>
  )
}


const Group = ({ children }: { children: ReactNode }) => <div className="card divide-y divide-line overflow-hidden">{children}</div>

function Row({ label, value, onClick, icon, danger }: { label: string; value?: string; onClick: () => void; icon?: ReactNode; danger?: boolean }) {
  return (
    <button onClick={onClick} className={`flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-pink-50 ${danger ? 'text-pink-600' : ''}`}>
      {icon}<span className="flex-1 font-semibold">{label}</span>
      {value && <span className="text-muted">{value}</span>}
      <ChevronRight size={18} className="text-muted" />
    </button>
  )
}

function Segmented({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <div className="inline-flex rounded-full bg-pink-50 p-1">
      {options.map(([v, l]) => (
        <button key={v} onClick={() => onChange(v)}
          className={`rounded-full px-3 py-1.5 text-sm font-bold transition ${value === v ? 'bg-pink-500 text-white shadow' : 'text-muted'}`}>{l}</button>
      ))}
    </div>
  )
}
