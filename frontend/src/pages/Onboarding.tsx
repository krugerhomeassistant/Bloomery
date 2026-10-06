import { useState } from 'react'
import { subDays } from 'date-fns'
import { format, t , N_ } from '../i18n'
import { ChevronLeft } from 'lucide-react'
import { api, iso, type User } from '../api'
import { useApp } from '../state'
import { Logo, Stepper } from '../components/ui'

const GOALS = [
  { id: 'track', emoji: '🌸', title: N_('Track my cycle'), sub: N_('Predictions, symptoms and insights') },
  { id: 'conceive', emoji: '🍼', title: N_('Get pregnant'), sub: N_('Know your fertile window') },
  { id: 'avoid', emoji: '🛡️', title: N_('Understand my fertility'), sub: N_('Not a contraceptive method') },
] as const

export default function Onboarding() {
  const { user, setUser, bump } = useApp()
  const [step, setStep] = useState(0)
  const [goal, setGoal] = useState<User['goal']>('track')
  const [last, setLast] = useState<string | null>(null)
  const [unknown, setUnknown] = useState(false)
  const [plen, setPlen] = useState(5)
  const [clen, setClen] = useState(28)
  const [birth, setBirth] = useState<string>('')
  const [busy, setBusy] = useState(false)

  const finish = async () => {
    setBusy(true)
    const u = await api<User>('/api/profile', {
      method: 'PUT', today: false,
      body: { goal, period_length: plen, cycle_length: clen, onboarded: true, birth_year: birth ? +birth : null },
    })
    if (last && !unknown) await api('/api/period/start', { body: { day: last } })
    bump()
    setUser(u)
  }

  const days = Array.from({ length: 42 }, (_, i) => subDays(new Date(), 41 - i))
  const steps = [
    <div key="goal" className="space-y-3">
      <h1 className="text-2xl font-black">{t('Hi')} {user?.display_name || t('there')}{t('! What would you like Bloomery to help with?')}</h1>
      {GOALS.map((g) => (
        <button key={g.id} onClick={() => setGoal(g.id)}
          className={`card flex w-full items-center gap-4 p-4 text-left transition ${goal === g.id ? 'ring-2 ring-pink-500' : ''}`}>
          <span className="text-3xl">{g.emoji}</span>
          <span><span className="block font-extrabold">{t(g.title)}</span><span className="text-sm text-muted">{t(g.sub)}</span></span>
        </button>
      ))}
    </div>,
    <div key="last">
      <h1 className="mb-1 text-2xl font-black">{t('When did your last period start?')}</h1>
      <p className="mb-4 text-muted">{t('Tap the first day. You can change this later.')}</p>
      <div className="card grid grid-cols-7 gap-1 p-3">
        {days.map((d) => {
          const v = iso(d), sel = v === last
          return (
            <button key={v} onClick={() => { setLast(v); setUnknown(false) }}
              className={`flex aspect-square flex-col items-center justify-center rounded-full text-sm transition ${sel ? 'bg-pink-500 font-black text-white' : 'hover:bg-pink-100'}`}>
              <span className="text-[9px] uppercase opacity-60">{d.getDate() === 1 || v === iso(days[0]) ? format(d, 'MMM') : ''}</span>
              {d.getDate()}
            </button>
          )
        })}
      </div>
      <button onClick={() => { setUnknown(true); setLast(null) }} className={`mt-4 w-full text-center font-bold ${unknown ? 'text-pink-600' : 'text-muted'}`}>
        {unknown ? '✓ ' : ''}{t('I don\'t remember')}
      </button>
    </div>,
    <div key="plen" className="text-center">
      <h1 className="mb-2 text-2xl font-black">{t('How long does your period usually last?')}</h1>
      <p className="mb-10 text-muted">{t('Most periods last 3–7 days.')}</p>
      <Stepper value={plen} onChange={setPlen} min={1} max={12} unit={t('days')} />
    </div>,
    <div key="clen" className="text-center">
      <h1 className="mb-2 text-2xl font-black">{t('How long is your cycle usually?')}</h1>
      <p className="mb-10 text-muted">{t('From the first day of one period to the first day of the next. 21–35 days is typical.')}</p>
      <Stepper value={clen} onChange={setClen} min={15} max={90} unit={t('days')} />
    </div>,
    <div key="age" className="text-center">
      <h1 className="mb-2 text-2xl font-black">{t('What year were you born?')}</h1>
      <p className="mb-8 text-muted">{t('Optional — helps tailor insights.')}</p>
      <input className="input text-center text-2xl font-bold" inputMode="numeric" placeholder="e.g. 1994" maxLength={4}
        value={birth} onChange={(e) => setBirth(e.target.value.replace(/\D/g, ''))} />
    </div>,
  ]
  const last_step = step === steps.length - 1
  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col px-6 py-6">
      <div className="mb-6 flex items-center gap-3">
        {step > 0 ? (
          <button onClick={() => setStep(step - 1)} className="rounded-full p-1.5 hover:bg-pink-100" aria-label={t('Back')}><ChevronLeft /></button>
        ) : <Logo size={32} />}
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-pink-100">
          <div className="h-full rounded-full bg-pink-500 transition-all" style={{ width: `${((step + 1) / steps.length) * 100}%` }} />
        </div>
      </div>
      <div className="fade-in flex-1" key={step}>{steps[step]}</div>
      <button className="btn-primary mt-8 w-full" disabled={busy || (step === 1 && !last && !unknown)}
        onClick={() => (last_step ? finish() : setStep(step + 1))}>
        {last_step ? t('Let\'s go') : t('Next')}
      </button>
    </div>
  )
}
