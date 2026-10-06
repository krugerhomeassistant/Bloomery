import type { ReactNode } from 'react'
import { differenceInCalendarDays, parseISO } from 'date-fns'
import type { Overview } from '../api'

const THEMES: Record<string, { bg: string; fg: string; accent: string }> = {
  period: { bg: 'radial-gradient(circle at 30% 25%, #FF8FAB 0%, #FF4A7D 60%, #EB2F65 100%)', fg: '#fff', accent: '#fff' },
  late: { bg: 'radial-gradient(circle at 30% 25%, #FFA3B9 0%, #FF6F96 70%)', fg: '#fff', accent: '#fff' },
  due: { bg: 'radial-gradient(circle at 30% 25%, #FFA3B9 0%, #FF6F96 70%)', fg: '#fff', accent: '#fff' },
  fertile: { bg: 'radial-gradient(circle at 30% 25%, #7FE0D6 0%, #22ADA5 70%, #148F88 100%)', fg: '#fff', accent: '#fff' },
  cycle: { bg: 'radial-gradient(circle at 30% 25%, var(--color-card) 0%, var(--color-pink-50) 55%, var(--color-pink-100) 100%)', fg: 'var(--color-ink)', accent: '#FF4A7D' },
  pregnancy: { bg: 'radial-gradient(circle at 30% 25%, #C9B6FF 0%, #9B7BF0 65%, #7C5CE0 100%)', fg: '#fff', accent: '#fff' },
  empty: { bg: 'radial-gradient(circle at 30% 25%, var(--color-card) 0%, var(--color-pink-50) 55%, var(--color-pink-100) 100%)', fg: 'var(--color-ink)', accent: '#FF4A7D' },
}

export function CycleRing({ ov, children }: { ov: Overview | null; children?: ReactNode }) {
  const st = ov?.status
  const theme = THEMES[st?.state ?? 'empty'] ?? THEMES.cycle
  const S = 320, C = S / 2, R = 150
  const cur = ov?.current_cycle
  let arcs: ReactNode = null
  const preg = ov?.pregnancy
  if (preg) {  // progress through 280 days
    const pt = (day: number) => { const a = (day / 280) * 2 * Math.PI - Math.PI / 2; return [C + R * Math.cos(a), C + R * Math.sin(a)] }
    const d = Math.min(preg.days, 279), [x, y] = pt(d)
    arcs = (
      <>
        <path d={`M${C},${C - R} A${R},${R} 0 ${d > 140 ? 1 : 0} 1 ${x},${y}`} stroke="#9B7BF0" strokeWidth="9" fill="none" strokeLinecap="round" />
        <circle cx={x} cy={y} r="12" fill="var(--color-card)" stroke="#7C5CE0" strokeWidth="4" />
      </>
    )
  } else if (cur) {
    const len = cur.length
    const s0 = parseISO(cur.start)
    const pos = (iso: string) => differenceInCalendarDays(parseISO(iso), s0)
    const ang = (day: number) => (day / len) * 2 * Math.PI - Math.PI / 2
    const pt = (day: number, r = R) => [C + r * Math.cos(ang(day)), C + r * Math.sin(ang(day))]
    const arc = (a: number, b: number, color: string, key: string) => {
      const [x1, y1] = pt(a + 0.15), [x2, y2] = pt(b + 0.85)
      const large = b + 0.7 - a > len / 2 ? 1 : 0
      return <path key={key} d={`M${x1},${y1} A${R},${R} 0 ${large} 1 ${x2},${y2}`} stroke={color} strokeWidth="9" fill="none" strokeLinecap="round" />
    }
    const today = cur && ov ? pos(ov.today) : 0
    const [tx, ty] = pt(Math.min(today, len - 1) + 0.5)
    const [ox, oy] = pt(pos(cur.ovulation) + 0.5)
    arcs = (
      <>
        {arc(0, pos(cur.period_end), '#FF4A7D', 'p')}
        {!ov?.hormonal && arc(pos(cur.fertile_start), pos(cur.fertile_end), '#3CC4BB', 'f')}
        {!ov?.hormonal && <circle cx={ox} cy={oy} r="7" fill="#148F88" stroke="var(--color-canvas)" strokeWidth="3" />}
        <circle cx={tx} cy={ty} r="12" fill="var(--color-card)" stroke="#FF4A7D" strokeWidth="4" />
      </>
    )
  }
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[320px]">
      <svg viewBox={`0 0 ${S} ${S}`} className="absolute inset-0 h-full w-full overflow-visible">
        <circle cx={C} cy={C} r={R} stroke="var(--color-line)" strokeWidth="9" fill="none" />
        {arcs}
      </svg>
      <div
        className="absolute inset-[22px] flex flex-col items-center justify-center rounded-full px-8 text-center shadow-[0_20px_50px_-12px_rgba(255,74,125,0.35)] transition-all duration-500"
        style={{ background: theme.bg, color: theme.fg }}
      >
        <div className="text-base font-bold opacity-90">{st?.label ?? ' '}</div>
        <div className="my-0.5 text-[2.6rem] leading-tight font-black" style={{ color: st?.state === 'cycle' ? theme.accent : undefined }}>
          {st?.headline ?? '…'}
        </div>
        <div className="text-sm font-semibold opacity-80">{st?.sub}</div>
        {children && <div className="mt-4">{children}</div>}
      </div>
    </div>
  )
}
