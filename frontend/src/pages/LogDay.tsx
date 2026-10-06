import { useEffect, useMemo, useState } from 'react'
import { addDays, isToday, parseISO } from 'date-fns'
import { format, t } from '../i18n'
import { ChevronLeft, ChevronRight, Droplet, Search } from 'lucide-react'
import { api, iso, type DayLog } from '../api'
import { useApp } from '../state'
import { Chip, Sheet } from '../components/ui'

const cToF = (c: number) => +(c * 9 / 5 + 32).toFixed(2)
const fToC = (f: number) => +((f - 32) * 5 / 9).toFixed(2)
const LB = 2.20462

export default function LogDay() {
  const { logDay, openLog, catalog, user, bump, notify } = useApp()
  const [log, setLog] = useState<DayLog | null>(null)
  const [q, setQ] = useState('')
  const [nums, setNums] = useState({ temperature: '', weight: '', water: '', sleep: '' })
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState('')
  const F = user?.temp_unit === 'F', LBS = user?.weight_unit === 'lb'

  useEffect(() => {
    if (!logDay) return
    setLog(null)
    setErr('')
    api<DayLog>(`/api/logs/${logDay}`, { today: false }).then((l) => {
      setLog({ ...l, tags: l.tags ?? {} })
      setNums({
        temperature: l.temperature ? String(F ? cToF(l.temperature) : l.temperature) : '',
        weight: l.weight ? String(LBS ? +(l.weight * LB).toFixed(1) : l.weight) : '',
        water: l.water_ml ? String(l.water_ml) : '',
        sleep: l.sleep_hours ? String(l.sleep_hours) : '',
      })
    })
  }, [logDay, F, LBS])

  const toggle = (cat: string, id: string) => {
    if (!log) return
    const cur = new Set(log.tags[cat] ?? [])
    // exclusive "none" style options
    const exclusive = ['none', 'fine']
    if (cur.has(id)) cur.delete(id)
    else {
      if (exclusive.includes(id)) cur.clear()
      else exclusive.forEach((x) => cur.delete(x))
      cur.add(id)
    }
    setLog({ ...log, tags: { ...log.tags, [cat]: [...cur] } })
  }

  const cats = useMemo(() => {
    const s = q.trim().toLowerCase()
    return (catalog?.categories ?? [])
      .map((c) => ({ ...c, items: s ? c.items.filter((i) => i.label.toLowerCase().includes(s)) : c.items }))
      .filter((c) => c.items.length)
  }, [catalog, q])

  const apply = async () => {
    if (!log || !logDay) return
    setSaving(true)
    setErr('')
    const n = (v: string) => (v.trim() === '' ? null : Number(v.replace(',', '.')))
    const t = n(nums.temperature), w = n(nums.weight)
    try {
      const r = await api<{ note?: string | null }>(`/api/logs/${logDay}`, {
        method: 'PUT', today: false,
        body: {
          flow: log.flow, tags: log.tags, notes: log.notes ?? '',
          temperature: t == null ? null : F ? fToC(t) : t,
          weight: w == null ? null : LBS ? +(w / LB).toFixed(2) : w,
          water_ml: n(nums.water), sleep_hours: n(nums.sleep),
        },
      })
      bump()
      openLog(null)
      if (r.note) notify(r.note)
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setSaving(false)
    }
  }

  const d = logDay ? parseISO(logDay) : new Date()
  const title = (
    <div className="flex items-center gap-1">
      <button className="rounded-full p-1 hover:bg-pink-100" onClick={() => openLog(iso(addDays(d, -1)))} aria-label={t('Previous day')}><ChevronLeft size={20} /></button>
      <span className="min-w-28 text-center">{isToday(d) ? t('Today') : format(d, 'EEE, MMM d')}</span>
      <button className="rounded-full p-1 hover:bg-pink-100 disabled:opacity-30" disabled={isToday(d)} onClick={() => openLog(iso(addDays(d, 1)))} aria-label={t('Next day')}><ChevronRight size={20} /></button>
    </div>
  )

  return (
    <Sheet open={!!logDay} onClose={() => openLog(null)} title={title} full>
      {!log || !catalog ? (
        <div className="p-10 text-center text-muted">{t('Loading…')}</div>
      ) : (
        <div className="space-y-4 px-4 pb-28">
          <label className="flex items-center gap-2 rounded-2xl bg-card px-4 py-3 shadow-sm">
            <Search size={18} className="text-muted" />
            <input className="flex-1 bg-transparent outline-none" placeholder={t('Search symptoms, moods…')} value={q} onChange={(e) => setQ(e.target.value)} />
          </label>

          {!q && (
            <Section title={t('Menstrual flow')} color="#FF4A7D">
              {catalog.flow.map((f) => (
                <Chip key={f.id} active={log.flow === f.id} emoji={<Drops n={f.id} on={log.flow === f.id} />} label={f.label} color="#FF4A7D"
                  onClick={() => setLog({ ...log, flow: log.flow === f.id ? null : f.id })} />
              ))}
            </Section>
          )}

          {cats.map((c) => (
            <Section key={c.id} title={c.title} color={c.color}>
              {c.items.map((i) => (
                <Chip key={i.id} active={(log.tags[c.id] ?? []).includes(i.id)} emoji={i.emoji} label={i.label} color={c.color}
                  onClick={() => toggle(c.id, i.id)} />
              ))}
            </Section>
          ))}

          {!q && (
            <div className="card space-y-3 p-4">
              <h3 className="font-extrabold">{t('Measurements')}</h3>
              <Num label={t('Basal temperature ({u})', { u: F ? '°F' : '°C' })} value={nums.temperature} step="0.01" placeholder={F ? '97.7' : '36.5'}
                onChange={(v) => setNums({ ...nums, temperature: v })} />
              <Num label={t('Weight ({u})', { u: LBS ? 'lb' : 'kg' })} value={nums.weight} step="0.1" onChange={(v) => setNums({ ...nums, weight: v })} />
              <Num label={t('Water (ml)')} value={nums.water} step="50" onChange={(v) => setNums({ ...nums, water: v })} />
              <Num label={t('Sleep (hours)')} value={nums.sleep} step="0.5" onChange={(v) => setNums({ ...nums, sleep: v })} />
              <div>
                <div className="mb-1 text-sm font-bold text-muted">{t('Notes')}</div>
                <textarea className="input min-h-24" value={log.notes ?? ''} placeholder={t('Anything else worth remembering?')}
                  onChange={(e) => setLog({ ...log, notes: e.target.value })} />
              </div>
            </div>
          )}
          {err && <p className="text-center text-sm font-bold text-pink-600">{err}</p>}
          <div className="fixed inset-x-0 bottom-0 mx-auto max-w-md bg-gradient-to-t from-canvas via-canvas to-transparent px-4 pb-safe pt-6">
            <button className="btn-primary mb-2 w-full" onClick={apply} disabled={saving}>{t('Apply')}</button>
          </div>
        </div>
      )}
    </Sheet>
  )
}

function Section({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <h3 className="mb-3 flex items-center gap-2 font-extrabold"><span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />{title}</h3>
      <div className="no-scrollbar -mx-1 flex gap-1 overflow-x-auto px-1 pb-1">{children}</div>
    </div>
  )
}

function Num({ label, value, onChange, step, placeholder }: { label: string; value: string; onChange: (v: string) => void; step: string; placeholder?: string }) {
  return (
    <label className="flex items-center justify-between gap-3">
      <span className="text-sm font-bold text-muted">{label}</span>
      <input className="input w-32 py-2 text-right" type="number" inputMode="decimal" step={step} placeholder={placeholder} value={value}
        onChange={(e) => onChange(e.target.value)} />
    </label>
  )
}

const DROPS: Record<string, number> = { spotting: 0, light: 1, medium: 2, heavy: 3 }
function Drops({ n, on }: { n: string; on: boolean }) {
  const c = on ? '#fff' : '#FF4A7D'
  if (!DROPS[n]) return <span className="block h-2.5 w-2.5 rounded-full" style={{ background: c }} />
  return (
    <span className="flex -space-x-1">
      {Array.from({ length: DROPS[n] }, (_, i) => <Droplet key={i} size={DROPS[n] > 2 ? 15 : 18} fill={c} color={c} />)}
    </span>
  )
}
