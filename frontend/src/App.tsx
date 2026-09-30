import { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { BarChart3, CalendarDays, Flower2, Sparkles, User as UserIcon } from 'lucide-react'
import { api, type User } from './api'
import { useApp } from './state'
import { Spinner } from './components/ui'
import Auth from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Today from './pages/Today'
import Calendar from './pages/Calendar'
import Insights from './pages/Insights'
import Assistant from './pages/Assistant'
import Profile from './pages/Profile'
import LogDay from './pages/LogDay'

const TABS = [
  { to: '/', label: 'Today', icon: Flower2 },
  { to: '/calendar', label: 'Calendar', icon: CalendarDays },
  { to: '/insights', label: 'Insights', icon: BarChart3 },
  { to: '/assistant', label: 'Assistant', icon: Sparkles },
  { to: '/profile', label: 'Profile', icon: UserIcon },
]

export default function App() {
  const { user, setUser, toast, notify } = useApp()
  const [ready, setReady] = useState(false)

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
      <div className="mx-auto flex min-h-full max-w-md flex-col">
        <main className="flex-1 pb-[var(--nav-h)]">
          <Routes>
            <Route path="/" element={<Today />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
        <nav className="pb-safe fixed inset-x-0 bottom-0 z-30 h-[var(--nav-h)] mx-auto max-w-md border-t border-line bg-card/95 backdrop-blur">
          <div className="grid grid-cols-5">
            {TABS.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} end={to === '/'}
                className={({ isActive }) => `flex flex-col items-center gap-0.5 pt-2.5 pb-1 text-[11px] font-bold transition ${isActive ? 'text-pink-500' : 'text-muted'}`}>
                {({ isActive }) => (<><Icon size={23} strokeWidth={isActive ? 2.5 : 2} />{label}</>)}
              </NavLink>
            ))}
          </div>
        </nav>
        <LogDay />
        {toast && (
          <button onClick={() => notify(null)} className="sheet-in fixed inset-x-3 bottom-[calc(var(--nav-h)+0.75rem)] z-40 mx-auto flex max-w-md gap-3 rounded-3xl bg-ink p-4 text-left text-sm text-canvas shadow-2xl">
            <span className="text-lg">💬</span><span>{toast}</span>
          </button>
        )}
      </div>
    </BrowserRouter>
  )
}
