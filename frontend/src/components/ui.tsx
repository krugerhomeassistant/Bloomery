import { useEffect, type ReactNode } from 'react'
import { X, Minus, Plus } from 'lucide-react'
import { t } from '../i18n'

export function Logo({ size = 40 }: { size?: number }) {
  return <img src="/icon.svg" width={size} height={size} alt="Bloomery" className="rounded-[28%]" />
}

export function Sheet({ open, onClose, title, children, full }: {
  open: boolean; onClose: () => void; title?: ReactNode; children: ReactNode; full?: boolean
}) {
  useEffect(() => {
    if (!open) return
    const k = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    addEventListener('keydown', k)
    document.body.style.overflow = 'hidden'
    return () => {
      removeEventListener('keydown', k)
      document.body.style.overflow = ''
    }
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/30 fade-in" onClick={onClose}>
      <div
        className={`sheet-in w-full max-w-md bg-canvas ${full ? 'h-[100dvh] sm:h-[94dvh] sm:rounded-t-[2rem]' : 'max-h-[90dvh] rounded-t-[2rem]'} flex flex-col overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        {title !== undefined && (
          <div className="flex items-center justify-between px-5 pt-4 pb-2">
            <div className="text-lg font-extrabold">{title}</div>
            <button onClick={onClose} className="rounded-full p-2 hover:bg-pink-100" aria-label={t('Close')}>
              <X size={22} />
            </button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto no-scrollbar">{children}</div>
      </div>
    </div>
  )
}

export function Chip({ active, onClick, emoji, label, color }: {
  active: boolean; onClick: () => void; emoji?: ReactNode; label: string; color?: string
}) {
  return (
    <button
      onClick={onClick}
      className="flex w-[76px] shrink-0 flex-col items-center gap-1.5 text-center transition active:scale-95"
    >
      <span
        className="grid h-14 w-14 place-items-center rounded-full text-2xl transition"
        style={{
          background: active ? color ?? '#FF4A7D' : 'var(--color-card)',
          boxShadow: active ? `0 6px 16px ${(color ?? '#FF4A7D') + '55'}` : 'inset 0 0 0 1.5px var(--color-line)',
        }}
      >
        <span className={active ? 'drop-shadow' : 'grayscale-[30%]'}>{emoji}</span>
      </span>
      <span className={`text-[11.5px] leading-tight ${active ? 'font-bold' : 'text-muted'}`}>{label}</span>
    </button>
  )
}

export function Stepper({ value, onChange, min, max, unit }: {
  value: number; onChange: (v: number) => void; min: number; max: number; unit: string
}) {
  return (
    <div className="flex items-center justify-center gap-6">
      <button className="grid h-12 w-12 place-items-center rounded-full bg-pink-100 text-pink-600" onClick={() => onChange(Math.max(min, value - 1))} aria-label={t('Decrease')}>
        <Minus />
      </button>
      <div className="min-w-24 text-center">
        <div className="text-5xl font-black text-pink-500">{value}</div>
        <div className="text-muted">{unit}</div>
      </div>
      <button className="grid h-12 w-12 place-items-center rounded-full bg-pink-100 text-pink-600" onClick={() => onChange(Math.min(max, value + 1))} aria-label={t('Increase')}>
        <Plus />
      </button>
    </div>
  )
}

export function LineChart({ points, color = '#FF4A7D', unit = '', height = 140 }: {
  points: { date: string; value: number }[]; color?: string; unit?: string; height?: number
}) {
  if (points.length < 2) return <div className="py-6 text-center text-sm text-muted">{t('Log at least two values to see a chart.')}</div>
  const W = 320, H = height, P = 24
  const vs = points.map((p) => p.value)
  const lo = Math.min(...vs), hi = Math.max(...vs), span = hi - lo || 1
  const x = (i: number) => P + (i / (points.length - 1)) * (W - 2 * P)
  const y = (v: number) => H - P - ((v - lo) / span) * (H - 2 * P)
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
      <text x={4} y={y(hi) + 4} fontSize="10" fill="currentColor" className="text-muted">{hi.toFixed(2)}{unit}</text>
      <text x={4} y={y(lo) + 4} fontSize="10" fill="currentColor" className="text-muted">{lo.toFixed(2)}{unit}</text>
      <path d={`${d} L${x(points.length - 1)},${H - P} L${x(0)},${H - P} Z`} fill={color} opacity=".1" />
      <path d={d} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      {points.map((p, i) => <circle key={p.date} cx={x(i)} cy={y(p.value)} r="3.5" fill="var(--color-card)" stroke={color} strokeWidth="2" />)}
    </svg>
  )
}

export function Spinner() {
  return <div className="mx-auto my-10 h-8 w-8 animate-spin rounded-full border-4 border-pink-200 border-t-pink-500" />
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-3 mt-7 flex items-end justify-between px-1">
      <h2 className="text-lg font-extrabold">{children}</h2>
      {action}
    </div>
  )
}
