import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, type Catalog, type User } from './api'

type Ctx = {
  user: User | null
  setUser: (u: User | null) => void
  catalog: Catalog | null
  version: number // bump to refetch data-dependent views
  bump: () => void
  logDay: string | null // open log sheet for date
  openLog: (d: string | null) => void
  theme: Theme
  setTheme: (t: Theme) => void
  toast: string | null
  notify: (msg: string | null) => void
}
type Theme = 'system' | 'light' | 'dark'

const AppCtx = createContext<Ctx>(null!)
export const useApp = () => useContext(AppCtx)

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [version, setVersion] = useState(0)
  const [logDay, openLog] = useState<string | null>(null)
  const [theme, setThemeState] = useState<Theme>(() => (localStorage.getItem('theme') as Theme) || 'system')
  const bump = useCallback(() => setVersion((v) => v + 1), [])
  const [toast, notify] = useState<string | null>(null)
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => notify(null), Math.max(10000, toast.length * 90))  // ~reading speed, min 10 s
    return () => clearTimeout(t)
  }, [toast])

  useEffect(() => {
    api<Catalog>('/api/catalog', { today: false }).then(setCatalog).catch(() => {})
  }, [])

  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)')
    const apply = () => document.documentElement.classList.toggle('dark', theme === 'dark' || (theme === 'system' && mq.matches))
    apply()
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [theme])

  const setTheme = (t: Theme) => {
    try {
      localStorage.setItem('theme', t)
    } catch {}
    setThemeState(t)
  }

  return (
    <AppCtx.Provider value={{ user, setUser, catalog, version, bump, logDay, openLog, theme, setTheme, toast, notify }}>{children}</AppCtx.Provider>
  )
}

// ---------------------------------------------------------------- app lock timing (per device)
export const LOCK_CHOICES: [number, string][] = [[1, '1 minute'], [5, '5 minutes'], [15, '15 minutes'], [60, '1 hour'], [240, '4 hours']]
const ls = (k: string) => { try { return localStorage.getItem(k) } catch { return null } }
export const lockAfterMin = () => Number(ls('lockAfter')) || 15
export const setLockAfter = (m: number) => { try { localStorage.setItem('lockAfter', String(m)) } catch {} }
export const markActive = () => { try { localStorage.setItem('lastActive', String(Date.now())) } catch {} }
export const idleTooLong = () => Date.now() - Number(ls('lastActive') || 0) > lockAfterMin() * 60_000

/** Fetch JSON, refetching whenever deps or global data version change. */
export function useFetch<T>(path: string | null, deps: unknown[] = []) {
  const { version } = useApp()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    if (!path) return
    let alive = true
    setLoading(true)
    api<T>(path)
      .then((d) => alive && (setData(d), setError(null)))
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, version, ...deps])
  return { data, error, loading, setData }
}
