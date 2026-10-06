import { Fragment, createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, type Catalog, type User } from './api'
import { N_, getLang, setLang, setWords, swap, type Lang } from './i18n'

type Ctx = {
  user: User | null
  setUser: (u: User | null) => void
  catalog: Catalog | null
  version: number // bump to refetch data-dependent views
  bump: () => void
  logDay: string | null // open log sheet for date
  openLog: (d: string | null) => void
  lang: Lang
  changeLang: (l: Lang) => void
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
  const [lang, setLangState] = useState<Lang>(getLang)
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

  // the account's language wins once signed in; before that the browser's / last used one applies
  useEffect(() => {
    if (user?.lang && user.lang !== getLang()) { setLang(user.lang); setLangState(user.lang) }
  }, [user?.lang])
  const [wordsKey, setWordsKey] = useState('')  // re-render everything when the user's own words change
  useEffect(() => {
    const k = JSON.stringify(user?.words ?? [])
    if (k !== wordsKey) { setWords(user?.words ?? []); setWordsKey(k) }
  }, [user?.words, wordsKey])
  const wk = wordsKey === '[]' ? '' : wordsKey
  const changeLang = (l: Lang) => {
    setLang(l)
    setLangState(l)
    if (user) api('/api/language', { method: 'PUT', body: { lang: l }, today: false }).then(() => setUser({ ...user, lang: l })).catch(() => {})
  }
  useEffect(() => {
    api<Catalog>(`/api/catalog?lang=${lang}`, { today: false }).then(setCatalog).catch(() => {})
  }, [lang])
  // symptom / mood names come from the server catalog, so the user's words are applied here too
  const shownCatalog = catalog && (wk
    ? { flow: catalog.flow.map((i) => ({ ...i, label: swap(i.label) })), categories: catalog.categories.map((c) => ({ ...c, title: swap(c.title), items: c.items.map((i) => ({ ...i, label: swap(i.label) })) })) }
    : catalog)

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
    <AppCtx.Provider value={{ user, setUser, catalog: shownCatalog, version, bump, logDay, openLog, lang, changeLang, theme, setTheme, toast, notify }}>
      <Fragment key={lang + wk}>{children}</Fragment>
    </AppCtx.Provider>
  )
}

// ---------------------------------------------------------------- app lock timing (per device)
export const LOCK_CHOICES: [number, string][] = [[1, N_('1 minute')], [5, N_('5 minutes')], [15, N_('15 minutes')], [60, N_('1 hour')], [240, N_('4 hours')]]
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
