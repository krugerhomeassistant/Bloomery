import { differenceInCalendarDays, format, parseISO } from 'date-fns'
import { AlertCircle, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Overview } from '../api'
import { useApp, useFetch } from '../state'
import { LineChart, SectionTitle, Spinner } from '../components/ui'
import RecapSheet from '../components/RecapSheet'
import { CycleTrend, SymptomMap, type Heatmap } from '../components/InsightCharts'
import { useState } from 'react'

type Hist = { start: string; length: number | null; days_so_far: number | null; period_length: number; ovulation: string; ovulation_confirmed: boolean }
type Data = {
  stats: { cycles_tracked: number; avg_cycle_length: number | null; avg_period_length: number | null; min_cycle: number | null; max_cycle: number | null; regularity: string; history: Hist[] }
  flags: { level: string; title: string; text: string }[]
  symptoms: { patterns: { tag: string; label: string; phase: string; count: number; share: number }[]; top: { tag: string; label: string; count: number }[] }
  heatmap: Heatmap
  temperature: { date: string; value: number }[]
  weight: { date: string; value: number }[]
  overview: Overview
}
const PHASE_LABEL: Record<string, string> = { menstrual: 'during your period', follicular: 'after your period', fertile: 'around ovulation', luteal: 'before your period' }

export default function Insights() {
  const { data } = useFetch<Data>('/api/insights')
  const [recap, setRecap] = useState<string | null>(null)
  const { catalog, user } = useApp()
  if (!data) return <Spinner />
  const { stats, overview: ov } = data
  const emoji = (tag: string) => {
    const [c, i] = tag.split(':')
    return catalog?.categories.find((x) => x.id === c)?.items.find((x) => x.id === i)?.emoji ?? '•'
  }
  const maxLen = Math.max(35, ...stats.history.map((h) => h.length ?? h.days_so_far ?? 0))
  const F = user?.temp_unit === 'F', LBS = user?.weight_unit === 'lb'

  return (
    <div className="px-4 pt-4 pb-8">
      <div className="flex items-center justify-between px-1">
        <h1 className="text-2xl font-black">Insights</h1>
        <Link to="/report" className="btn-ghost px-4 py-2 text-sm"><FileText size={16} /> Doctor's report</Link>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <Tile label="Average cycle" value={stats.avg_cycle_length ?? ov.predicted_cycle_length} unit="days" sub={stats.avg_cycle_length ? `${stats.min_cycle}–${stats.max_cycle} day range` : 'from your settings'} />
        <Tile label="Average period" value={stats.avg_period_length ?? ov.predicted_period_length} unit="days" sub={stats.avg_period_length ? 'from history' : 'from your settings'} />
        <Tile label="Cycle regularity" value={stats.regularity === 'unknown' ? '—' : stats.regularity} sub={stats.regularity === 'unknown' ? 'Needs 3+ cycles' : `${stats.cycles_tracked} cycles tracked`} small />
        <Tile label="Luteal phase" value={ov.luteal_length} unit="days" sub="used for ovulation" />
      </div>

      {data.flags.length > 0 && (
        <>
          <SectionTitle>Health check</SectionTitle>
          <div className="space-y-3">
            {data.flags.map((f) => (
              <div key={f.title} className="card flex gap-3 p-4">
                <AlertCircle className={`shrink-0 ${f.level === 'warn' ? 'text-pink-500' : 'text-teal-500'}`} />
                <div><div className="font-extrabold">{f.title}</div><div className="text-sm text-muted">{f.text}</div></div>
              </div>
            ))}
          </div>
        </>
      )}

      <SectionTitle>Cycle length over time</SectionTitle>
      <div className="card p-4"><CycleTrend history={stats.history} /></div>

      <SectionTitle>Cycle history</SectionTitle>
      <div className="card space-y-4 p-4">
        {stats.history.length === 0 && <p className="text-sm text-muted">Log your periods to build your cycle history.</p>}
        {stats.history.map((h) => {
          const len = h.length ?? h.days_so_far ?? 0
          const ovDay = differenceInCalendarDays(parseISO(h.ovulation), parseISO(h.start))
          return (
            <button key={h.start} onClick={() => setRecap(h.start)} className="block w-full rounded-2xl text-left transition hover:bg-pink-50/60 active:scale-[0.99]">
              <div className="mb-1.5 flex justify-between text-sm">
                <span className="font-extrabold">{h.length ? `${h.length} days` : 'Current cycle'}</span>
                <span className="text-muted">{format(parseISO(h.start), 'MMM d, yyyy')}</span>
              </div>
              <div className="relative h-3.5 rounded-full bg-pink-50" style={{ width: `${(len / maxLen) * 100}%`, minWidth: '2rem' }}>
                <div className="absolute inset-y-0 left-0 rounded-full bg-pink-500" style={{ width: `${(h.period_length / Math.max(len, 1)) * 100}%` }} />
                {ovDay < len && (
                  <div className={`absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 rounded-full ${h.ovulation_confirmed ? 'bg-teal-600' : 'bg-teal-400'}`}
                    style={{ left: `calc(${(ovDay / Math.max(len, 1)) * 100}% - 7px)` }} title={h.ovulation_confirmed ? 'Ovulation (BBT-confirmed)' : 'Estimated ovulation'} />
                )}
              </div>
              <div className="mt-1 flex justify-between text-xs text-muted"><span>Period {h.period_length} days</span><span className="font-bold text-[#7C5CE0]">✨ Recap</span></div>
            </button>
          )
        })}
      </div>

      <RecapSheet start={recap} onClose={() => setRecap(null)} />

      <SectionTitle>Symptom map</SectionTitle>
      <div className="card p-4"><SymptomMap map={data.heatmap} emoji={emoji} /></div>

      <SectionTitle>Your body patterns</SectionTitle>
      <div className="card p-4">
        {data.symptoms.patterns.length === 0 && data.symptoms.top.length === 0 && (
          <p className="text-sm text-muted">Log symptoms and moods for a few cycles and Bloomery will spot patterns for you.</p>
        )}
        <div className="space-y-3">
          {data.symptoms.patterns.map((p) => (
            <div key={p.tag} className="flex items-center gap-3">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-pink-50 text-xl">{emoji(p.tag)}</span>
              <div className="text-sm"><b>{p.label}</b> usually shows up <b className={p.phase === 'fertile' ? 'text-teal-500' : 'text-pink-500'}>{PHASE_LABEL[p.phase] ?? p.phase}</b> <span className="text-muted">· {Math.round(p.share * 100)}% of the time</span></div>
            </div>
          ))}
        </div>
        {data.symptoms.top.length > 0 && (
          <>
            <div className="mb-2 mt-5 text-xs font-extrabold uppercase text-muted">Most logged</div>
            <div className="flex flex-wrap gap-2">
              {data.symptoms.top.map((t) => (
                <span key={t.tag} className="rounded-full bg-pink-50 px-3 py-1.5 text-sm font-semibold">{emoji(t.tag)} {t.label} <span className="text-muted">×{t.count}</span></span>
              ))}
            </div>
          </>
        )}
      </div>

      <SectionTitle>Basal body temperature · this cycle</SectionTitle>
      <div className="card p-4">
        <LineChart color="#22ADA5" unit={F ? '°F' : '°C'} points={data.temperature.map((p) => ({ ...p, value: F ? p.value * 9 / 5 + 32 : p.value }))} />
      </div>

      <SectionTitle>Weight · last 6 months</SectionTitle>
      <div className="card p-4">
        <LineChart unit={LBS ? 'lb' : 'kg'} points={data.weight.map((p) => ({ ...p, value: LBS ? p.value * 2.20462 : p.value }))} />
      </div>

      <p className="mt-6 px-2 text-center text-xs text-muted">Predictions are estimates based on your logs and are not a method of contraception or a medical diagnosis.</p>
    </div>
  )
}

function Tile({ label, value, unit, sub, small }: { label: string; value: string | number; unit?: string; sub: string; small?: boolean }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-extrabold uppercase text-muted">{label}</div>
      <div className={`mt-1 font-black capitalize text-pink-500 ${small ? 'text-xl leading-8' : 'text-3xl'}`}>
        {value}{unit && <span className="ml-1 text-base text-muted">{unit}</span>}
      </div>
      <div className="text-xs text-muted">{sub}</div>
    </div>
  )
}
