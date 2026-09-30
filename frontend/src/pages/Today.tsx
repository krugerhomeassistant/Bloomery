import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { addDays, format, isToday, parseISO, startOfWeek } from 'date-fns'
import { CalendarDays, Plus, RefreshCw, Sparkles, AlertCircle } from 'lucide-react'
import { api, iso, type DayInfo, type Overview } from '../api'
import { useApp, useFetch } from '../state'
import { CycleRing } from '../components/CycleRing'
import { SectionTitle, Sheet } from '../components/ui'
import RecapSheet from '../components/RecapSheet'

type Card = { kind: string; emoji: string; title: string; text: string; start?: string }
const CARD_BG: Record<string, string> = {
  note: 'bg-gradient-to-br from-[#F4ECFF] to-card dark:from-[#2B2340]',
  forecast: 'bg-gradient-to-br from-[#FFF4E5] to-card dark:from-[#3A2A1A]',
  milestone: 'bg-gradient-to-br from-teal-50 to-card',
  recap: 'bg-gradient-to-br from-[#EEF2FF] to-card dark:from-[#1E2340]',
}

const PHASE: Record<string, { name: string; emoji: string; text: string }> = {
  menstrual: { name: 'Menstrual phase', emoji: '🌺', text: 'Rest, warmth and iron-rich foods help.' },
  follicular: { name: 'Follicular phase', emoji: '🌱', text: 'Energy tends to rise as estrogen climbs.' },
  fertile: { name: 'Fertile window', emoji: '🌼', text: 'Chance of pregnancy is higher now.' },
  ovulation: { name: 'Ovulation', emoji: '✨', text: 'An egg is likely released today.' },
  luteal: { name: 'Luteal phase', emoji: '🌙', text: 'PMS symptoms may show up this week.' },
}

export default function Today() {
  const { user, openLog, bump } = useApp()
  const nav = useNavigate()
  const ov = useFetch<Overview>('/api/cycle/overview').data
  const weekStart = startOfWeek(new Date(), { weekStartsOn: 1 })
  const week = useFetch<DayInfo[]>(`/api/cycle/calendar?start=${iso(weekStart)}&end=${iso(addDays(weekStart, 6))}`).data
  const insights = useFetch<{ flags: { level: string; title: string; text: string }[]; stats: any }>('/api/insights').data
  const [refresh, setRefresh] = useState(0)
  const daily = useFetch<{ source: string; content: string; error?: string }>(`/api/ai/daily${refresh ? '?refresh=true' : ''}`, [refresh])
  const [showInsight, setShowInsight] = useState(false)
  const feed = useFetch<Card[]>('/api/feed').data
  const [card, setCard] = useState<Card | null>(null)
  const [recapStart, setRecapStart] = useState<string | null>(null)
  const [confirmStart, setConfirmStart] = useState(false)

  const st = ov?.status
  const inPeriod = st?.state === 'period'
  const logStart = async () => {
    await api('/api/period/start', { body: { day: iso(new Date()) } })
    setConfirmStart(false)
    bump()
  }
  const phase = PHASE[st?.phase ?? ''] ?? null

  return (
    <div className="px-4 pt-4">
      <header className="mb-2 flex items-center justify-between px-1">
        <div>
          <div className="text-sm font-semibold text-muted">{format(new Date(), 'EEEE, MMMM d')}</div>
          <h1 className="text-2xl font-black">Hi, {user?.display_name}</h1>
        </div>
        <button onClick={() => nav('/calendar')} className="grid h-11 w-11 place-items-center rounded-full bg-card shadow-sm" aria-label="Calendar">
          <CalendarDays size={20} className="text-pink-500" />
        </button>
      </header>

      {/* week strip */}
      <div className="mb-5 grid grid-cols-7 gap-1 px-1">
        {Array.from({ length: 7 }, (_, i) => {
          const d = addDays(weekStart, i)
          const info = week?.find((w) => w.date === iso(d))
          const k = info?.kind
          const today = isToday(d)
          return (
            <button key={i} onClick={() => openLog(iso(d))} className="flex flex-col items-center gap-1">
              <span className={`text-[11px] font-bold uppercase ${today ? 'text-ink' : 'text-muted'}`}>{today ? 'Today' : format(d, 'EEEEE')}</span>
              <span className={`grid h-9 w-9 place-items-center rounded-full text-sm font-bold transition
                ${k === 'period' ? 'bg-pink-500 text-white' : ''}
                ${k === 'predicted_period' ? 'border-2 border-dashed border-pink-400 text-pink-500' : ''}
                ${k === 'fertile' ? 'text-teal-500' : ''}
                ${k === 'ovulation' ? 'border-2 border-teal-400 text-teal-600' : ''}
                ${today && !k ? 'bg-ink text-canvas' : ''}
                ${today && k ? 'ring-2 ring-ink ring-offset-2 ring-offset-canvas' : ''}`}>
                {format(d, 'd')}
              </span>
            </button>
          )
        })}
      </div>

      <CycleRing ov={ov}>
        {st && (
          <button
            onClick={() => (inPeriod ? nav('/calendar?edit=1') : setConfirmStart(true))}
            className={`btn px-5 py-2.5 text-sm shadow-md ${['period', 'late', 'due', 'fertile'].includes(st.state) ? 'bg-white text-pink-600' : 'bg-pink-500 text-white'}`}
          >
            {inPeriod ? 'Edit period dates' : 'Log period'}
          </button>
        )}
      </CycleRing>

      <SectionTitle>My daily insights · <span className="text-muted">Today</span></SectionTitle>
      <div className="no-scrollbar -mx-4 flex gap-3 overflow-x-auto px-4 pb-2">
        <button onClick={() => openLog(iso(new Date()))}
          className="flex h-40 w-32 shrink-0 flex-col justify-between rounded-3xl bg-gradient-to-br from-pink-400 to-pink-500 p-4 text-left text-white shadow-lg shadow-pink-500/25">
          <span className="font-extrabold leading-tight">Log your symptoms</span>
          <span className="grid h-10 w-10 place-items-center self-end rounded-full bg-white/25"><Plus /></span>
        </button>
        <button onClick={() => setShowInsight(true)}
          className="card flex h-40 w-44 shrink-0 flex-col justify-between bg-gradient-to-br from-[#F4ECFF] to-[#FFE3EC] p-4 text-left dark:from-[#2B2340] dark:to-[#3A2130]">
          <span className="flex items-center gap-1.5 text-xs font-extrabold uppercase text-[#7C5CE0]"><Sparkles size={14} /> {daily.data?.source === 'ai' ? 'AI insight' : 'Insight'}</span>
          <span className="line-clamp-4 text-sm font-semibold">{daily.loading && !daily.data ? 'Thinking…' : daily.data?.content}</span>
        </button>
        {feed?.map((c) => (
          <button key={c.kind + c.title} onClick={() => (c.kind === 'recap' && c.start ? setRecapStart(c.start) : setCard(c))}
            className={`card flex h-40 w-40 shrink-0 flex-col justify-between p-4 text-left ${CARD_BG[c.kind] ?? ''}`}>
            <span className="text-3xl">{c.emoji}</span>
            <span><span className="block font-extrabold leading-tight">{c.title}</span>
              <span className="line-clamp-2 text-xs text-muted">{c.text}</span></span>
          </button>
        ))}
        {phase && (
          <div className="card flex h-40 w-36 shrink-0 flex-col justify-between p-4">
            <span className="text-3xl">{phase.emoji}</span>
            <span><span className="block font-extrabold leading-tight">{phase.name}</span><span className="text-xs text-muted">{phase.text}</span></span>
          </div>
        )}
        {st?.cycle_day && (
          <div className="card flex h-40 w-32 shrink-0 flex-col justify-between p-4">
            <span className="text-xs font-extrabold uppercase text-muted">Cycle day</span>
            <span className="text-5xl font-black text-pink-500">{st.cycle_day}</span>
            <span className="text-xs text-muted">of ~{ov?.predicted_cycle_length}</span>
          </div>
        )}
        {ov?.next_period && (
          <div className="card flex h-40 w-36 shrink-0 flex-col justify-between p-4">
            <span className="text-xs font-extrabold uppercase text-muted">Next period</span>
            <span className="text-2xl font-black">{format(parseISO(ov.next_period), 'MMM d')}</span>
            <span className="text-xs text-muted">± {ov.uncertainty_days} days</span>
          </div>
        )}
      </div>

      {insights?.flags?.length ? (
        <>
          <SectionTitle>Health check</SectionTitle>
          <div className="space-y-3">
            {insights.flags.map((f) => (
              <div key={f.title} className="card flex gap-3 p-4">
                <AlertCircle className={f.level === 'warn' ? 'shrink-0 text-pink-500' : 'shrink-0 text-teal-500'} />
                <div><div className="font-extrabold">{f.title}</div><div className="text-sm text-muted">{f.text}</div></div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {ov?.current_cycle && (
        <>
          <SectionTitle>Current cycle</SectionTitle>
          <div className="card grid grid-cols-3 divide-x divide-line p-4 text-center">
            <Stat label="Started" value={format(parseISO(ov.current_cycle.start), 'MMM d')} />
            <Stat label="Ovulation" value={format(parseISO(ov.current_cycle.ovulation), 'MMM d')} tone="teal" />
            <Stat label="Avg cycle" value={`${ov.predicted_cycle_length}d`} />
          </div>
        </>
      )}
      <div className="h-6" />

      <Sheet open={showInsight} onClose={() => setShowInsight(false)} title={<span className="flex items-center gap-2"><Sparkles className="text-[#7C5CE0]" size={20} /> Today's insight</span>}>
        <div className="px-5 pb-8">
          <p className="whitespace-pre-wrap leading-relaxed">{daily.data?.content}</p>
          {daily.data?.error && <p className="mt-3 text-xs text-muted">AI unavailable: {daily.data.error}</p>}
          {daily.data?.source === 'ai' && (
            <button className="btn-ghost mt-5 text-sm" disabled={daily.loading} onClick={() => setRefresh((r) => r + 1)}>
              <RefreshCw size={16} className={daily.loading ? 'animate-spin' : ''} /> Regenerate
            </button>
          )}
          <p className="mt-6 text-xs text-muted">Insights are informational and not medical advice.</p>
        </div>
      </Sheet>

      <Sheet open={!!card} onClose={() => setCard(null)} title={card && <span className="flex items-center gap-2"><span>{card.emoji}</span>{card.title}</span>}>
        <div className="px-5 pb-8">
          <p className="leading-relaxed">{card?.text}</p>
          {card?.kind === 'forecast' && (
            <button className="btn-ghost mt-5 text-sm" onClick={() => { setCard(null); openLog(iso(new Date())) }}>Log how you feel</button>
          )}
          <p className="mt-6 text-xs text-muted">Based on your own logs and cycle predictions. Not medical advice.</p>
        </div>
      </Sheet>

      <RecapSheet start={recapStart} onClose={() => setRecapStart(null)} />

      <Sheet open={confirmStart} onClose={() => setConfirmStart(false)} title="Did your period start today?">
        <div className="space-y-3 px-5 pb-8">
          <p className="text-muted">We'll mark today and the next few expected days. You can adjust the dates anytime in the calendar.</p>
          <button className="btn-primary w-full" onClick={logStart}>Yes, started today</button>
          <button className="btn-ghost w-full" onClick={() => nav('/calendar?edit=1')}>Pick other dates</button>
        </div>
      </Sheet>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: 'teal' }) {
  return (
    <div>
      <div className="text-xs font-bold text-muted">{label}</div>
      <div className={`text-lg font-black ${tone === 'teal' ? 'text-teal-500' : ''}`}>{value}</div>
    </div>
  )
}
