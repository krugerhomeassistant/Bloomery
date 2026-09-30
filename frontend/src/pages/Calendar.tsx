import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { addDays, addMonths, eachDayOfInterval, endOfMonth, format, getDay, isAfter, isToday, parseISO, startOfMonth } from 'date-fns'
import { Check, Plus } from 'lucide-react'
import { api, iso, type DayInfo } from '../api'
import { useApp, useFetch } from '../state'

const PHASE_NAME: Record<string, string> = {
  menstrual: 'Period', follicular: 'Follicular phase', fertile: 'Fertile window', ovulation: 'Ovulation day', luteal: 'Luteal phase',
}

export default function Calendar() {
  const { openLog, bump } = useApp()
  const [params, setParams] = useSearchParams()
  const edit = params.get('edit') === '1'
  const now = new Date()
  const first = startOfMonth(addMonths(now, -6)), last = endOfMonth(addMonths(now, 6))
  const { data } = useFetch<DayInfo[]>(`/api/cycle/calendar?start=${iso(first)}&end=${iso(last)}`)
  const byDate = useMemo(() => Object.fromEntries((data ?? []).map((d) => [d.date, d])), [data])
  const [selected, setSelected] = useState(iso(now))
  const [draft, setDraft] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const curRef = useRef<HTMLDivElement>(null)
  const editLimit = addDays(now, 14)

  useEffect(() => {
    curRef.current?.scrollIntoView({ block: 'start' })
  }, [data === null])

  useEffect(() => {
    if (edit && data) setDraft(new Set(data.filter((d) => d.kind === 'period').map((d) => d.date)))
  }, [edit, data])

  const months = Array.from({ length: 13 }, (_, i) => addMonths(first, i))
  const save = async () => {
    setSaving(true)
    const before = new Set((data ?? []).filter((d) => d.kind === 'period').map((d) => d.date))
    await api('/api/period', {
      method: 'PUT',
      body: { add: [...draft].filter((d) => !before.has(d)), remove: [...before].filter((d) => !draft.has(d)) },
    })
    setSaving(false)
    setParams({})
    bump()
  }
  const toggle = (d: string) => {
    const n = new Set(draft)
    n.has(d) ? n.delete(d) : n.add(d)
    setDraft(n)
  }
  const sel = byDate[selected]

  return (
    <div className="flex h-full flex-col">
      <div className="sticky top-0 z-10 bg-canvas px-4 pb-2 pt-4 shadow-[0_6px_12px_-10px_rgba(0,0,0,0.15)]">
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-2xl font-black">{edit ? 'Edit period' : 'Calendar'}</h1>
          {!edit && (
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => setParams({ edit: '1' })}>Edit period</button>
          )}
        </div>
        <div className="grid grid-cols-7 text-center text-xs font-bold text-muted">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => <div key={i}>{d}</div>)}
        </div>
      </div>

      <div className="flex-1 px-4 pb-72">
        {months.map((m) => {
          const days = eachDayOfInterval({ start: startOfMonth(m), end: endOfMonth(m) })
          const offset = (getDay(days[0]) + 6) % 7
          const isCur = format(m, 'yyyy-MM') === format(now, 'yyyy-MM')
          return (
            <div key={m.toISOString()} ref={isCur ? curRef : undefined} className="scroll-mt-24 pt-5">
              <div className="mb-2 px-1 text-lg font-extrabold">{format(m, 'MMMM yyyy')}</div>
              <div className="grid grid-cols-7 gap-y-1.5">
                {Array.from({ length: offset }, (_, i) => <div key={`e${i}`} />)}
                {days.map((d) => {
                  const v = iso(d), info = byDate[v], k = info?.kind
                  const today = isToday(d)
                  if (edit) {
                    const on = draft.has(v), disabled = isAfter(d, editLimit)
                    return (
                      <button key={v} disabled={disabled} onClick={() => toggle(v)} className="flex flex-col items-center gap-0.5 disabled:opacity-30">
                        <span className={`text-xs ${today ? 'font-black' : 'text-muted'}`}>{format(d, 'd')}</span>
                        <span className={`grid h-7 w-7 place-items-center rounded-full border-2 transition ${on ? 'border-pink-500 bg-pink-500 text-white' : 'border-pink-200'}`}>
                          {on && <Check size={16} strokeWidth={3} />}
                        </span>
                      </button>
                    )
                  }
                  return (
                    <button key={v} onClick={() => setSelected(v)} className="flex h-11 flex-col items-center justify-center">
                      <span className={`relative grid h-10 w-10 place-items-center rounded-full text-[15px] font-bold transition
                        ${k === 'period' ? 'bg-pink-500 text-white' : ''}
                        ${k === 'predicted_period' ? 'border-2 border-dashed border-pink-400 text-pink-500' : ''}
                        ${k === 'fertile' ? 'text-teal-500' : ''}
                        ${k === 'ovulation' ? 'border-2 border-dashed border-teal-400 bg-teal-50 text-teal-600' : ''}
                        ${selected === v ? 'ring-2 ring-ink ring-offset-2 ring-offset-canvas' : ''}
                        ${today ? 'underline decoration-2 underline-offset-4' : ''}`}>
                        {format(d, 'd')}
                        {info?.has_log && <span className="absolute -bottom-0.5 h-1.5 w-1.5 rounded-full bg-[#7C5CE0]" />}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* bottom panel */}
      <div className="fixed inset-x-0 bottom-[calc(var(--nav-h)+0.5rem)] z-20 mx-auto max-w-md px-3">
        {edit ? (
          <div className="card flex gap-3 p-3 shadow-xl">
            <button className="btn-ghost flex-1" onClick={() => setParams({})}>Cancel</button>
            <button className="btn-primary flex-1" disabled={saving} onClick={save}>Save</button>
          </div>
        ) : (
          sel && (
            <div className="card p-4 shadow-xl">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-bold text-muted">{format(parseISO(selected), 'EEEE, MMMM d')}</div>
                  <div className="text-xl font-black">
                    {sel.cycle_day ? `Cycle day ${sel.cycle_day}` : 'No cycle data'}
                  </div>
                  <div className="text-sm">
                    {sel.phase && <span className={sel.phase === 'fertile' || sel.phase === 'ovulation' ? 'text-teal-500 font-bold' : sel.phase === 'menstrual' ? 'text-pink-500 font-bold' : 'text-muted'}>{PHASE_NAME[sel.phase]}{sel.predicted && sel.phase === 'menstrual' && sel.kind !== 'period' ? ' (predicted)' : ''}</span>}
                    {sel.chance && <span className="text-muted"> · {sel.chance} chance of pregnancy</span>}
                  </div>
                </div>
                <button onClick={() => openLog(selected)} className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-pink-500 text-white shadow-lg shadow-pink-500/30" aria-label="Log">
                  <Plus />
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-[11px] font-semibold text-muted">
                <Legend cls="bg-pink-500" label="Period" />
                <Legend cls="border-2 border-dashed border-pink-400" label="Predicted" />
                <Legend cls="bg-teal-400" label="Fertile" />
                <Legend cls="border-2 border-dashed border-teal-400 bg-teal-50" label="Ovulation" />
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}

const Legend = ({ cls, label }: { cls: string; label: string }) => (
  <span className="flex items-center gap-1.5"><span className={`h-3 w-3 rounded-full ${cls}`} />{label}</span>
)
