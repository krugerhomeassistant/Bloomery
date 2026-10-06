import { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { BarChart3, CalendarDays, Flower2, Sparkles, User as UserIcon, X } from 'lucide-react'
import { api, type User } from './api'
import { idleTooLong, markActive, useApp } from './state'
import { Spinner } from './components/ui'
import Auth from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Today from './pages/Today'
import Calendar from './pages/Calendar'
import Insights from './pages/Insights'
import Assistant from './pages/Assistant'
import Profile from './pages/Profile'
import LogDay from './pages/LogDay'
import Report from './pages/Report'
import LockScreen from './components/LockScreen'
import { t , N_ } from './i18n'

const TABS = [
  { to: '/', label: N_('Today'), icon: Flower2 },
  { to: '/calendar', label: N_('Calendar'), icon: CalendarDays },
  { to: '/insights', label: N_('Insights'), icon: BarChart3 },
  { to: '/assistant', label: N_('Assistant'), icon: Sparkles },
  { to: '/profile', label: N_('Profile'), icon: UserIcon },
]

export default function App() {
  const { user, setUser, toast, notify } = useApp()
  const [ready, setReady] = useState(false)
  const [locked, setLocked] = useState(idleTooLong)  // only matters when user.pin_set

  useEffect(() => { if (ready && !user?.pin_set) setLocked(false) }, [ready, user])  // fresh password login = unlocked
  useEffect(() => {
    // lock only after being away longer than the chosen time (backgrounded or closed)
    const onVis = () => (document.hidden ? markActive() : idleTooLong() && setLocked(true))
    document.addEventListener('visibilitychange', onVis)
    addEventListener('pagehide', markActive)
    return () => { document.removeEventListener('visibilitychange', onVis); removeEventListener('pagehide', markActive) }
  }, [])

  useEffect(() => {
    api<User>('/api/auth/me', { today: false }).then(setUser).catch(() => setUser(null)).finally(() => setReady(true))
    const onUnauth = () => setUser(null)
    addEventListener('bloomery:unauthorized', onUnauth)
    return () => removeEventListener('bloomery:unauthorized', onUnauth)
  }, [setUser])

  if (!ready) return <div className="pt-40"><Spinner /></div>
  if (!user) return <Auth />
  if (!user.onboarded) return <Onboarding />

  return (
    <BrowserRouter>
      <div className="mx-auto flex min-h-full max-w-md flex-col print:max-w-none">
        <main className="flex-1 pb-[var(--nav-h)]">
          <Routes>
            <Route path="/" element={<Today />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/report" element={<Report />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
        <nav className="pb-safe fixed inset-x-0 bottom-0 z-30 h-[var(--nav-h)] mx-auto max-w-md border-t border-line bg-card/95 backdrop-blur">
          <div className="grid grid-cols-5">
            {TABS.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} end={to === '/'}
                className={({ isActive }) => `flex flex-col items-center gap-0.5 pt-2.5 pb-1 text-[11px] font-bold transition ${isActive ? 'text-pink-500' : 'text-muted'}`}>
                {({ isActive }) => (<><Icon size={23} strokeWidth={isActive ? 2.5 : 2} />{t(label)}</>)}
              </NavLink>
            ))}
          </div>
        </nav>
        <LogDay />
        {user.pin_set && locked && <LockScreen onUnlock={() => { markActive(); setLocked(false) }} />}
        {toast && (
          <div role="status" className="sheet-in fixed inset-x-3 bottom-[calc(var(--nav-h)+0.75rem)] z-40 mx-auto flex max-w-md items-start gap-3 rounded-3xl bg-ink p-4 text-left text-sm text-canvas shadow-2xl">
            <span className="text-lg">💬</span><span className="flex-1">{toast}<span className="mt-1 block text-xs opacity-60">{t('Saved to today\'s insights')}</span></span>
            <button onClick={() => notify(null)} className="-m-1 rounded-full p-1 opacity-70 hover:opacity-100" aria-label={t('Dismiss')}><X size={18} /></button>
          </div>
        )}
      </div>
    </BrowserRouter>
  )
}
