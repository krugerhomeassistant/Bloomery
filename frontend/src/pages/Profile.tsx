import { useRef, useState, type ReactNode } from 'react'
import { Bell, ChevronRight, Download, LogOut, Moon, Sparkles, Trash2, Upload, KeyRound, Lock } from 'lucide-react'
import { api, iso, type LifeStage, type Overview, type User } from '../api'
import { useApp, useFetch } from '../state'
import { SectionTitle, Sheet, Stepper } from '../components/ui'
import { extractAppleHealth } from '../appleHealth'
import AiSettings from '../components/AiSettings'
import NotifySettings from '../components/NotifySettings'

const STAGE_HELP: Record<LifeStage, string> = {
  cycle: 'Period and fertility predictions from your logs.',
  pregnancy: 'Shows your pregnancy week, due date and weekly tips instead of period predictions. Your cycle history is kept.',
  perimenopause: 'Expects irregular cycles: wider prediction ranges, days since your last period and the 12-month menopause marker.',
}

export default function Profile() {
  const { user, setUser, bump, theme, setTheme } = useApp()
  const ov = useFetch<Overview>('/api/cycle/overview').data
  const share = useFetch<{ token: string | null }>('/api/tokens/share')
  const ha = useFetch<{ token: string | null }>('/api/tokens/ha')
  const [copied, setCopied] = useState(false)
  const ai = useFetch<{ enabled: boolean; provider: string; model: string | null; local: boolean }>('/api/ai/status').data
  const [editing, setEditing] = useState<null | 'cycle_length' | 'period_length' | 'luteal_length'>(null)
  const [val, setVal] = useState(0)
  const [pw, setPw] = useState<null | { current: string; new: string; msg?: string }>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [lock, setLock] = useState<null | { pin: string; password: string; msg?: string }>(null)
  const [msg, setMsg] = useState('')
  const [aiOpen, setAiOpen] = useState(false)
  const [notifyOpen, setNotifyOpen] = useState(false)
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
      if (/\.zip$/i.test(f.name)) throw new Error('Unzip the Apple Health export first, then pick apple_health_export/export.xml')
      if (/\.xml$/i.test(f.name)) {
        setMsg('Reading Apple Health export… 0%')
        const data = await extractAppleHealth(f, (p) => setMsg(`Reading Apple Health export… ${p}%`))
        if (!data.records.length) throw new Error('No cycle data (menstruation, symptoms, temperature) found in this export')
        const r = await api<{ days: number; period_days: number; first: string; last: string }>('/api/import/other', { body: { content: JSON.stringify(data) }, today: false })
        setMsg(`Imported ${r.days} days from Apple Health (${r.period_days} period days, ${r.first} → ${r.last})`)
        bump()
        return
      }
      const text = await f.text()
      let j: any = null
      try { j = JSON.parse(text) } catch {}
      if (j?.app === 'bloomery') {
        const r = await api<{ imported: number }>('/api/import', { body: { logs: j.logs ?? [], replace: false }, today: false })
        setMsg(`Imported ${r.imported} days`)
      } else {
        const r = await api<{ source: string; days: number; first: string; last: string }>('/api/import/other', { body: { content: text }, today: false })
        setMsg(`Imported ${r.days} period days from ${r.source} (${r.first} → ${r.last})`)
      }
      bump()
    } catch (e: any) {
      setMsg(`Import failed: ${e.message}`)
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
  const haYaml = haUrl ? HA_YAML(`${haUrl}?tz=${tz}`) : ''
  const LABEL = { cycle_length: 'Cycle length', period_length: 'Period length', luteal_length: 'Luteal phase length' }
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

      <SectionTitle>Life stage</SectionTitle>
      <Group>
        <div className="px-4 py-3">
          <Segmented value={user.mode} onChange={(v) => setStage(v as LifeStage, v === 'pregnancy' ? user.lmp : null)}
            options={[['cycle', 'Cycle'], ['pregnancy', 'Pregnancy'], ['perimenopause', 'Perimenopause']]} />
          {user.mode === 'pregnancy' && (
            <label className="mt-3 flex items-center justify-between gap-3 text-sm font-bold text-muted">First day of last period
              <input type="date" className="input w-auto py-1.5" value={user.lmp ?? ov?.pregnancy?.lmp ?? ''} max={iso(new Date())}
                onChange={(e) => e.target.value && setStage('pregnancy', e.target.value)} />
            </label>
          )}
        </div>
      </Group>
      <p className="mt-2 px-2 text-xs text-muted">{STAGE_HELP[user.mode]}</p>

      <SectionTitle>Cycle settings</SectionTitle>
      <Group>
        {(['cycle_length', 'period_length', 'luteal_length'] as const).map((k) => (
          <Row key={k} label={LABEL[k]} onClick={() => { setVal(user[k]); setEditing(k) }}
            value={`${user[k]} days${ov && LEARNED[k](ov) !== user[k] ? ` · using ${LEARNED[k](ov)}` : ''}`} />
        ))}
        <div className="px-4 py-3">
          <div className="mb-2 text-sm font-bold text-muted">Goal</div>
          <Segmented value={user.goal} onChange={(v) => save({ goal: v as User['goal'] })}
            options={[['track', 'Track cycle'], ['conceive', 'Get pregnant'], ['avoid', 'Understand fertility']]} />
        </div>
      </Group>
      <p className="mt-2 px-2 text-xs text-muted">These are your starting defaults. Once you've logged enough cycles, Bloomery uses what it learned from your history ("using …").</p>

      <SectionTitle>Preferences</SectionTitle>
      <Group>
        <div className="space-y-3 px-4 py-3">
          <div className="flex items-center justify-between"><span className="font-semibold">Temperature</span>
            <Segmented value={user.temp_unit} onChange={(v) => save({ temp_unit: v as 'C' | 'F' })} options={[['C', '°C'], ['F', '°F']]} /></div>
          <div className="flex items-center justify-between"><span className="font-semibold">Weight</span>
            <Segmented value={user.weight_unit} onChange={(v) => save({ weight_unit: v as 'kg' | 'lb' })} options={[['kg', 'kg'], ['lb', 'lb']]} /></div>
          <div className="flex items-center justify-between"><span className="flex items-center gap-2 font-semibold"><Moon size={18} /> Theme</span>
            <Segmented value={theme} onChange={(v) => setTheme(v as any)} options={[['system', 'Auto'], ['light', 'Light'], ['dark', 'Dark']]} /></div>
        </div>
      </Group>

      <SectionTitle>AI assistant</SectionTitle>
      <Group>
        <button onClick={() => setAiOpen(true)} className="flex w-full items-center gap-3 px-4 py-4 text-left hover:bg-pink-50">
          <Sparkles className="shrink-0 text-[#7C5CE0]" />
          <div className="flex-1 text-sm">
            {ai?.enabled ? <><b>On</b> · {ai.provider} · {ai.model}<div className="text-muted">{ai.local ? 'Runs on your server — data never leaves it.' : 'Cycle summaries are sent to this cloud provider.'}</div></>
              : <><b>Off</b><div className="text-muted">Tap to connect Claude, OpenAI or another provider.</div></>}
          </div>
          <ChevronRight size={18} className="text-muted" />
        </button>
      </Group>
      <AiSettings open={aiOpen} onClose={() => setAiOpen(false)} />

      <SectionTitle>Notifications</SectionTitle>
      <Group>
        <Row icon={<Bell size={18} className="text-pink-500" />} label="Daily reminders & heads-ups" onClick={() => setNotifyOpen(true)} />
      </Group>
      <NotifySettings open={notifyOpen} onClose={() => setNotifyOpen(false)} />

      <SectionTitle>Partner sharing</SectionTitle>
      <Group>
        <div className="space-y-3 px-4 py-4 text-sm">
          <p className="text-muted">A private, read-only link showing where you are in your cycle, your predicted period and fertile days, plus tips for your partner. Symptoms, moods, sex and notes are never shared.</p>
          {shareUrl ? (
            <>
              <div className="select-all break-all rounded-2xl bg-pink-50 p-3 font-mono text-xs">{shareUrl}</div>
              <div className="flex flex-wrap gap-2">
                {window.isSecureContext && navigator.clipboard && (
                  <button className="btn-primary px-4 py-2 text-sm" onClick={() => navigator.clipboard.writeText(shareUrl).then(() => setCopied(true))}>{copied ? 'Copied!' : 'Copy link'}</button>
                )}
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => shareAct('POST')}>New link</button>
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => shareAct('DELETE')}>Stop sharing</button>
              </div>
            </>
          ) : (
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => shareAct('POST')}>Create share link</button>
          )}
        </div>
      </Group>

      <SectionTitle>Home Assistant & calendar</SectionTitle>
      <Group>
        <div className="space-y-3 px-4 py-4 text-sm">
          <p className="text-muted">Private read-only feeds: sensors for Home Assistant (cycle day, phase, days until period, fertile window) and a calendar of your periods, fertile windows and ovulation. No symptoms or notes.</p>
          {haUrl ? (
            <>
              <div className="font-bold">1. Sensors: add to <code>configuration.yaml</code> and restart HA</div>
              <pre className="select-all overflow-x-auto rounded-2xl bg-pink-50 p-3 font-mono text-[11px] leading-snug">{haYaml}</pre>
              <div className="font-bold">2. Calendar: HA → Settings → Devices & services → Add → <i>Remote Calendar</i> (or subscribe in any calendar app)</div>
              <div className="select-all break-all rounded-2xl bg-pink-50 p-3 font-mono text-xs">{haUrl}/calendar.ics?tz={tz}</div>
              <div className="flex flex-wrap gap-2">
                {window.isSecureContext && navigator.clipboard && (
                  <button className="btn-primary px-4 py-2 text-sm" onClick={() => navigator.clipboard.writeText(haYaml).then(() => setCopied(true))}>{copied ? 'Copied!' : 'Copy YAML'}</button>
                )}
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => tokenAct('ha', 'POST')}>New token</button>
                <button className="btn-ghost px-4 py-2 text-sm" onClick={() => tokenAct('ha', 'DELETE')}>Turn off</button>
              </div>
            </>
          ) : (
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => tokenAct('ha', 'POST')}>Create feed</button>
          )}
        </div>
      </Group>

      <SectionTitle>Your data</SectionTitle>
      <Group>
        <Row icon={<Download size={18} />} label="Export data (JSON)" onClick={exportData} />
        <Row icon={<Upload size={18} />} label="Import data (Flo, Clue, Apple Health, CSV)" onClick={() => file.current?.click()} />
        <Row icon={<Lock size={18} />} label="App lock (PIN)" value={user.pin_set ? 'On' : 'Off'} onClick={() => setLock({ pin: '', password: '' })} />
        <Row icon={<KeyRound size={18} />} label="Change password" onClick={() => setPw({ current: '', new: '' })} />
        <Row icon={<LogOut size={18} />} label="Log out" onClick={logout} />
        <Row icon={<Trash2 size={18} />} label="Delete account & all data" danger onClick={() => setConfirmDelete(true)} />
      </Group>
      <input ref={file} type="file" accept=".json,.csv,.cluedata,.xml,.zip,application/json,text/csv,text/xml" hidden onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) importData(f) }} />
      {msg && <p className="mt-3 text-center text-sm font-bold text-pink-600">{msg}</p>}
      <p className="mt-8 text-center text-xs text-muted">Bloomery · self-hosted · your data stays yours</p>

      <Sheet open={!!editing} onClose={() => setEditing(null)} title={editing ? LABEL[editing] : ''}>
        {editing && (
          <div className="px-5 pb-8 pt-4">
            <Stepper value={val} onChange={setVal} min={RANGE[editing][0]} max={RANGE[editing][1]} unit="days" />
            <button className="btn-primary mt-8 w-full" onClick={async () => { await save({ [editing]: val }); setEditing(null) }}>Save</button>
          </div>
        )}
      </Sheet>

      <Sheet open={!!lock} onClose={() => setLock(null)} title="App lock">
        {lock && (
          <form className="space-y-3 px-5 pb-8" onSubmit={async (e) => {
            e.preventDefault()
            const remove = (e.nativeEvent as SubmitEvent).submitter?.getAttribute('value') === 'remove'
            try {
              setUser(await api<User>('/api/auth/pin', { method: 'PUT', body: { password: lock.password, pin: remove ? null : lock.pin }, today: false }))
              setLock(null); setMsg(remove ? 'App lock turned off' : 'PIN saved. Bloomery locks when opened or after a minute in the background.')
            } catch (err: any) { setLock({ ...lock, msg: err.message }) }
          }}>
            <p className="text-sm text-muted">Asks for a 4-digit PIN when Bloomery opens or returns after a minute in the background. 5 wrong tries sign you out.</p>
            <input className="input text-center text-2xl tracking-[.5em]" type="password" inputMode="numeric" pattern="\d{4}" maxLength={4} autoComplete="off"
              placeholder="••••" value={lock.pin} onChange={(e) => setLock({ ...lock, pin: e.target.value.replace(/\D/g, '') })} required={!user.pin_set} />
            <input className="input" type="password" placeholder="Account password" autoComplete="current-password" value={lock.password} onChange={(e) => setLock({ ...lock, password: e.target.value })} required />
            {lock.msg && <p className="text-sm font-bold text-pink-600">{lock.msg}</p>}
            <button className="btn-primary w-full" disabled={lock.pin.length !== 4}>{user.pin_set ? 'Change PIN' : 'Set PIN'}</button>
            {user.pin_set && <button value="remove" formNoValidate className="btn-ghost w-full">Turn off app lock</button>}
          </form>
        )}
      </Sheet>

      <Sheet open={!!pw} onClose={() => setPw(null)} title="Change password">
        {pw && (
          <form className="space-y-3 px-5 pb-8" onSubmit={async (e) => {
            e.preventDefault()
            try { await api('/api/auth/password', { body: { current: pw.current, new: pw.new }, today: false }); setPw(null); setMsg('Password changed') }
            catch (err: any) { setPw({ ...pw, msg: err.message }) }
          }}>
            <input className="input" type="password" placeholder="Current password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} />
            <input className="input" type="password" placeholder="New password (min 8)" minLength={8} value={pw.new} onChange={(e) => setPw({ ...pw, new: e.target.value })} />
            {pw.msg && <p className="text-sm font-bold text-pink-600">{pw.msg}</p>}
            <button className="btn-primary w-full">Update</button>
          </form>
        )}
      </Sheet>

      <Sheet open={confirmDelete} onClose={() => setConfirmDelete(false)} title="Delete everything?">
        <div className="space-y-3 px-5 pb-8">
          <p className="text-muted">This permanently deletes your account, all logs and chat history from this server. Export first if you want a backup.</p>
          <button className="btn w-full bg-pink-600 text-white" onClick={async () => { await api('/api/account', { method: 'DELETE', today: false }); setUser(null) }}>Delete permanently</button>
          <button className="btn-ghost w-full" onClick={() => setConfirmDelete(false)}>Cancel</button>
        </div>
      </Sheet>
    </div>
  )
}

const HA_YAML = (url: string) => `rest:
  - resource: ${url}
    scan_interval: 900
    sensor:
      - name: Bloomery cycle day
        unique_id: bloomery_cycle_day
        icon: mdi:flower
        value_template: "{{ value_json.cycle_day }}"
        json_attributes: [phase, label, headline, summary, next_period, ovulation, pregnancy_chance]
      - name: Bloomery phase
        unique_id: bloomery_phase
        icon: mdi:moon-waning-crescent
        value_template: "{{ value_json.phase }}"
      - name: Bloomery days until period
        unique_id: bloomery_days_until_period
        icon: mdi:calendar-heart
        unit_of_measurement: d
        value_template: "{{ value_json.days_until_period }}"
    binary_sensor:
      - name: Bloomery period
        unique_id: bloomery_period
        icon: mdi:water
        value_template: "{{ value_json.in_period }}"
      - name: Bloomery fertile window
        unique_id: bloomery_fertile
        icon: mdi:flower-tulip
        value_template: "{{ value_json.fertile }}"`

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
