import { useEffect, useState, type FormEvent } from 'react'
import { api, type User } from '../api'
import { useApp } from '../state'
import { Logo } from '../components/ui'
import { t } from '../i18n'

export default function Auth() {
  const { setUser } = useApp()
  const [regOpen, setRegOpen] = useState(false)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [f, setF] = useState({ username: '', password: '', display_name: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api<{ registration_open: boolean }>('/api/auth/status', { today: false }).then((s) => {
      setRegOpen(s.registration_open)
      if (s.registration_open) setMode('register')
    })
  }, [])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setErr('')
    try {
      setUser(await api<User>(`/api/auth/${mode}`, { body: f, today: false }))
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-full flex-col items-center justify-center bg-gradient-to-b from-pink-100 to-canvas px-6 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <Logo size={72} />
          <h1 className="text-3xl font-black">{t('Bloomery')}</h1>
          <p className="text-muted">{t('Your cycle, your server, your data.')}</p>
        </div>
        <form onSubmit={submit} className="card space-y-3 p-6">
          <h2 className="mb-1 text-xl font-extrabold">{mode === 'login' ? t('Welcome back') : t('Create your account')}</h2>
          {mode === 'register' && (
            <input className="input" placeholder={t('Your name')} value={f.display_name} onChange={(e) => setF({ ...f, display_name: e.target.value })} />
          )}
          <input className="input" placeholder={t('Username')} autoComplete="username" required value={f.username}
            onChange={(e) => setF({ ...f, username: e.target.value })} />
          <input className="input" placeholder={t('Password (min 8 characters)')} type="password" required minLength={8}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={f.password}
            onChange={(e) => setF({ ...f, password: e.target.value })} />
          {err && <p className="text-sm font-semibold text-pink-600">{err}</p>}
          <button className="btn-primary w-full" disabled={busy}>{mode === 'login' ? t('Log in') : t('Sign up')}</button>
          {regOpen && (
            <button type="button" className="w-full pt-1 text-sm font-bold text-pink-500" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
              {mode === 'login' ? t('New here? Create an account') : t('Already have an account? Log in')}
            </button>
          )}
        </form>
        <p className="mt-6 text-center text-xs text-muted">{t('Self-hosted · no tracking · no ads')}</p>
      </div>
    </div>
  )
}
