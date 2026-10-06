import { useEffect, useState } from 'react'
import { addDays, format, getDay, parseISO } from 'date-fns'
import { Heart } from 'lucide-react'
import { api, type Overview, type Pregnancy, type Status } from '../api'
import { CycleRing } from '../components/CycleRing'
import { Logo, Spinner } from '../components/ui'

type View = {
  name: string; today: string; status: Status; current_cycle: Overview['current_cycle']; predicted_cycle_length: number
  next_period: string | null; phase: string | null; tip: string | null; pregnancy?: Pregnancy | null; hormonal?: boolean; days: { date: string; kind: string | null }[]
}
const KIND: Record<string, string> = {
  period: 'bg-pink-500 text-white', predicted_period: 'border-2 border-dashed border-pink-400 text-pink-500',
  fertile: 'text-teal-500 font-black', ovulation: 'border-2 border-dashed border-teal-400 bg-teal-50 text-teal-600',
}

/** Read-only partner view, opened from a share link. No login. */
export default function SharePage({ token }: { token: string }) {
  const [v, setV] = useState<View | null>(null)
  const [err, setErr] = useState('')
  useEffect(() => { api<View>(`/api/share/${token}`).then(setV).catch((e) => setErr(e.message)) }, [token])

  if (err) return <div className="flex min-h-full flex-col items-center justify-center gap-4 p-8 text-center"><Logo size={56} /><p className="text-muted">{err}</p></div>
  if (!v) return <div className="pt-40"><Spinner /></div>

  const start = parseISO(v.days[0].date)
  const offset = (getDay(start) + 6) % 7
  return (
    <div className="mx-auto max-w-md px-4 pt-6 pb-10">
      <header className="mb-4 flex items-center gap-3 px-1">
        <Logo size={36} />
        <div><div className="text-sm font-semibold text-muted">Shared with you</div><h1 className="text-2xl font-black">{v.name}'s cycle</h1></div>
      </header>

      <CycleRing ov={{ ...v, luteal_length: 14, predicted_period_length: 5, uncertainty_days: 2, upcoming: [], mode: v.pregnancy ? 'pregnancy' : 'cycle', pregnancy: v.pregnancy ?? null, hormonal: !!v.hormonal } as Overview} />

      {v.tip && (
        <div className="card mt-6 flex gap-3 p-4">
          <Heart className="shrink-0 text-pink-500" />
          <div><div className="font-extrabold">How you can help</div><p className="text-sm text-muted">{v.tip}</p></div>
        </div>
      )}

      <div className="card mt-4 p-4">
        <div className="mb-3 flex justify-between text-sm">
          <span className="font-extrabold">Next 5 weeks</span>
          {v.next_period && <span className="text-muted">Next period ~{format(parseISO(v.next_period), 'MMM d')}</span>}
        </div>
        <div className="grid grid-cols-7 gap-y-1.5 text-center text-xs font-bold text-muted">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => <div key={i}>{d}</div>)}
          {Array.from({ length: offset }, (_, i) => <div key={`e${i}`} />)}
          {v.days.map((d, i) => (
            <div key={d.date} className="flex justify-center">
              <span className={`grid h-9 w-9 place-items-center rounded-full text-sm ${d.kind ? KIND[d.kind] : 'text-ink'} ${i === 0 ? 'ring-2 ring-ink ring-offset-2 ring-offset-card' : ''}`}>
                {format(addDays(start, i), 'd')}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-3 text-[11px] font-semibold text-muted">
          <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-pink-500" />Period</span>
          <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full border-2 border-dashed border-pink-400" />Predicted</span>
          <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-teal-400" />Fertile</span>
        </div>
      </div>
      <p className="mt-6 text-center text-xs text-muted">Shared privately from Bloomery · predictions are estimates, not contraception</p>
    </div>
  )
}
