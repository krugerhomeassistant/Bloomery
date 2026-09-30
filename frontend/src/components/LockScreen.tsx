import { useEffect, useState } from 'react'
import { Delete } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../state'
import { Logo } from './ui'

export default function LockScreen({ onUnlock }: { onUnlock: () => void }) {
  const { user, setUser } = useApp()
  const [pin, setPin] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const press = (k: string) => {
    if (busy) return
    const next = k === '<' ? pin.slice(0, -1) : (pin + k).slice(0, 4)
    setErr(''); setPin(next)
    if (next.length < 4) return
    setBusy(true)
    api('/api/auth/pin/verify', { body: { pin: next }, today: false })
      .then(onUnlock)
      .catch((e) => { setErr(e.message); setPin('') })
      .finally(() => setBusy(false))
  }
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (/^\d$/.test(e.key)) press(e.key); else if (e.key === 'Backspace') press('<') }
    addEventListener('keydown', onKey)
    return () => removeEventListener('keydown', onKey)
  })
  const logout = async () => { await api('/api/auth/logout', { method: 'POST', today: false }).catch(() => {}); setUser(null) }

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-canvas px-8 pb-safe">
      <Logo size={56} />
      <h1 className="mt-4 text-xl font-black">Hi {user?.display_name}, enter your PIN</h1>
      <div className="my-8 flex gap-4">
        {[0, 1, 2, 3].map((i) => <span key={i} className={`h-4 w-4 rounded-full border-2 border-pink-500 ${i < pin.length ? 'bg-pink-500' : ''}`} />)}
      </div>
      <p className="-mt-4 mb-4 h-5 text-sm font-bold text-pink-600">{err}</p>
      <div className="grid w-full max-w-[18rem] grid-cols-3 gap-4">
        {['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', '<'].map((k) => k ? (
          <button key={k} onClick={() => press(k)} aria-label={k === '<' ? 'Delete' : k}
            className="grid aspect-square place-items-center rounded-full bg-card text-2xl font-bold shadow-sm active:bg-pink-100">
            {k === '<' ? <Delete /> : k}
          </button>
        ) : <span key="gap" />)}
      </div>
      <button onClick={logout} className="mt-8 text-sm font-bold text-muted">Forgot PIN? Log in with password</button>
    </div>
  )
}
