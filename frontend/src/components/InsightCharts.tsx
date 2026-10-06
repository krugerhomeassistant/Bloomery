import { useState } from 'react'
import { format, parseISO } from 'date-fns'

type Hist = { start: string; length: number | null; period_length: number }
export type Heatmap = { days: number; cycles: number; period_days: number; ovulation_day: number | null; rows: { tag: string; label: string; share: number[] }[] }

const PINK = '#FF4A7D', TEAL = '#22ADA5'

/** Completed cycle lengths over time: dots + thin line (zoomed y-axis is honest for points, not bars), dashed average, typical 21–35 band. */
export function CycleTrend({ history }: { history: Hist[] }) {
  const done = history.filter((h) => h.length).slice(0, 12).reverse()
  const [sel, setSel] = useState<number | null>(null)
  if (done.length < 2) return <p className="text-sm text-muted">Shows up once you have two complete cycles.</p>
  const lens = done.map((h) => h.length!)
  const avg = lens.reduce((a, b) => a + b, 0) / lens.length
  const lo = Math.min(21, ...lens) - 2, hi = Math.max(35, ...lens) + 2
  const W = 320, H = 150, L = 26, B = 18, T = 8
  const y = (v: number) => T + (H - T - B) * (1 - (v - lo) / (hi - lo))
  const slot = (W - L) / done.length
  const cx = (i: number) => L + slot * i + slot / 2
  const shown = sel ?? done.length - 1
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between text-sm">
        <span><b>{done[shown].length} days</b> <span className="text-muted">· started {format(parseISO(done[shown].start), 'd MMM yyyy')}</span></span>
        <span className="text-xs text-muted">avg {avg.toFixed(1)} · ±{Math.round(Math.max(...lens) - Math.min(...lens)) / 2} d</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Cycle lengths: ${lens.join(', ')} days; average ${avg.toFixed(1)}`}>
        <rect x={L} y={y(35)} width={W - L} height={y(21) - y(35)} fill={TEAL} opacity={0.08} />
        {[21, 28, 35].map((v) => (
          <g key={v}>
            <line x1={L} x2={W} y1={y(v)} y2={y(v)} stroke="var(--color-line)" strokeWidth={1} />
            <text x={L - 4} y={y(v) + 3} textAnchor="end" fontSize={9} fill="var(--color-muted)">{v}</text>
          </g>
        ))}
        <polyline points={done.map((h, i) => `${cx(i)},${y(h.length!)}`).join(' ')} fill="none" stroke={PINK} strokeWidth={2} strokeLinejoin="round" opacity={0.5} />
        {done.map((h, i) => (
          <g key={h.start} onClick={() => setSel(i)} onMouseEnter={() => setSel(i)} className="cursor-pointer">
            <rect x={L + slot * i} y={T} width={slot} height={H - T - B} fill="transparent" />
            <circle cx={cx(i)} cy={y(h.length!)} r={i === shown ? 6 : 4.5} fill={PINK} stroke="var(--color-card)" strokeWidth={2} />
          </g>
        ))}
        <line x1={L} x2={W} y1={y(avg)} y2={y(avg)} stroke="var(--color-ink)" strokeWidth={1.5} strokeDasharray="4 3" opacity={0.6} />
        <text x={L + 2} y={H - 4} fontSize={9} fill="var(--color-muted)">{format(parseISO(done[0].start), 'MMM yy')}</text>
        <text x={W} y={H - 4} fontSize={9} textAnchor="end" fill="var(--color-muted)">{format(parseISO(done[done.length - 1].start), 'MMM yy')}</text>
      </svg>
      <div className="mt-1 flex gap-4 text-xs text-muted">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: PINK }} />Cycle length</span>
        <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed border-ink/60" />Your average</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-4 rounded-sm" style={{ background: TEAL, opacity: 0.25 }} />Typical 21–35</span>
      </div>
    </div>
  )
}

/** Symptom map: how often each top symptom/mood is logged on each cycle day (share of cycles). */
export function SymptomMap({ map, emoji }: { map: Heatmap; emoji: (tag: string) => string }) {
  const [sel, setSel] = useState<{ r: number; d: number } | null>(null)
  if (!map.rows.length) return <p className="text-sm text-muted">Log symptoms and moods for a couple of cycles to see when they tend to show up.</p>
  const cols = `7rem repeat(${map.days}, minmax(0, 1fr))`
  const row = sel && map.rows[sel.r]
  return (
    <div>
      <p className="mb-3 h-10 text-sm">{row
        ? <><b>{row.label}</b> on cycle day {sel.d + 1}: logged in <b>{Math.round(row.share[sel.d] * 100)}%</b> of your cycles</>
        : <span className="text-muted">Darker = more often. Tap a square for details. Based on {map.cycles} cycle{map.cycles === 1 ? '' : 's'}.</span>}</p>
      <div className="grid gap-[2px]" style={{ gridTemplateColumns: cols }}>
        <span className="text-[10px] font-bold text-muted">Phase</span>
        {Array.from({ length: map.days }, (_, d) => (
          <span key={d} className="h-1.5 self-end rounded-full" title={d < map.period_days ? 'Period' : d + 1 === map.ovulation_day ? 'Ovulation' : undefined}
            style={{ background: d < map.period_days ? PINK : map.ovulation_day && Math.abs(d + 1 - map.ovulation_day) <= 2 ? TEAL : 'var(--color-line)', opacity: d + 1 === map.ovulation_day ? 1 : 0.7 }} />
        ))}
        {map.rows.map((r, ri) => [
          <span key={r.tag} className="truncate pr-1 text-xs font-semibold leading-4" title={r.label}>{emoji(r.tag)} {r.label}</span>,
          ...r.share.map((v, d) => (
            <button key={`${r.tag}-${d}`} onClick={() => setSel({ r: ri, d })} aria-label={`${r.label}, cycle day ${d + 1}: ${Math.round(v * 100)}% of cycles`}
              className={`h-4 rounded-[3px] ${sel?.r === ri && sel.d === d ? 'ring-2 ring-ink ring-offset-1 ring-offset-card' : ''}`}
              style={{ background: v > 0 ? PINK : 'var(--color-line)', opacity: v > 0 ? 0.18 + 0.82 * v : 0.35 }} />
          )),
        ])}
        <span />
        {Array.from({ length: map.days }, (_, d) => (
          <span key={d} className="text-center text-[9px] text-muted">{[1, 7, 14, 21, 28, 35].includes(d + 1) ? d + 1 : ''}</span>
        ))}
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-muted">
        <span>Cycle day</span>
        <span className="flex items-center gap-1">Less {[0.18, 0.45, 0.72, 1].map((o) => <span key={o} className="h-2.5 w-2.5 rounded-[2px]" style={{ background: PINK, opacity: o }} />)} More</span>
      </div>
    </div>
  )
}
