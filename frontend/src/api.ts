import { format } from 'date-fns'

export const iso = (d: Date) => format(d, 'yyyy-MM-dd')
export const todayIso = () => iso(new Date())

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export async function api<T = any>(path: string, opts: { method?: string; body?: unknown; today?: boolean } = {}): Promise<T> {
  const url = new URL(path, location.origin)
  if (opts.today !== false && !url.searchParams.has('today')) url.searchParams.set('today', todayIso())
  const r = await fetch(url, {
    method: opts.method ?? (opts.body !== undefined ? 'POST' : 'GET'),
    credentials: 'same-origin',
    headers: opts.body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })
  if (!r.ok) {
    let msg = r.statusText
    try {
      const j = await r.json()
      msg = typeof j.detail === 'string' ? j.detail : Array.isArray(j.detail) ? j.detail.map((d: any) => d.msg).join(', ') : msg
    } catch {}
    if (r.status === 401) window.dispatchEvent(new Event('bloomery:unauthorized'))
    throw new ApiError(r.status, msg)
  }
  return r.json()
}

// ---------------------------------------------------------------- types
export type User = {
  id: number
  username: string
  display_name: string
  onboarded: boolean
  cycle_length: number
  period_length: number
  luteal_length: number
  goal: 'track' | 'conceive' | 'avoid'
  birth_year: number | null
  temp_unit: 'C' | 'F'
  weight_unit: 'kg' | 'lb'
  pin_set: boolean
}
export type Item = { id: string; label: string; emoji: string }
export type Catalog = { flow: Item[]; categories: { id: string; title: string; color: string; items: Item[] }[] }
export type Status = { state: string; label: string; headline: string; sub: string; cycle_day?: number; phase?: string; chance?: string }
export type Segment = {
  start: string; end: string; length: number; period_end: string; ovulation: string
  fertile_start: string; fertile_end: string; predicted: boolean; ovulation_confirmed: boolean
}
export type Overview = {
  today: string; status: Status; predicted_cycle_length: number; predicted_period_length: number
  luteal_length: number; uncertainty_days: number; next_period: string | null
  current_cycle: Segment | null; upcoming: Segment[]
}
export type DayInfo = {
  date: string; cycle_day: number | null; phase: string | null; chance: string | null
  kind: 'period' | 'predicted_period' | 'fertile' | 'ovulation' | null; predicted?: boolean; flow?: string | null; has_log?: boolean
}
export type DayLog = {
  day: string; flow: string | null; tags: Record<string, string[]>; temperature?: number | null; weight?: number | null
  water_ml?: number | null; sleep_hours?: number | null; notes: string
}
