import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowUp, Sparkles, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, todayIso } from '../api'
import { useFetch } from '../state'
import { t , N_ } from '../i18n'

type Msg = { role: 'user' | 'assistant'; content: string }
const SUGGESTIONS = [
  N_('When is my next period likely?'),
  N_('Why do I feel so tired before my period?'),
  N_('What patterns do you see in my symptoms?'),
  N_('When is my fertile window this cycle?'),
  N_('Tips for easing cramps?'),
]

export default function Assistant() {
  const status = useFetch<{ enabled: boolean; provider: string; model: string | null; local: boolean }>('/api/ai/status').data
  const hist = useFetch<Msg[]>('/api/ai/chat')
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => { if (hist.data) setMsgs(hist.data) }, [hist.data])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, busy])

  const send = async (m: string) => {
    if (!m.trim() || busy) return
    setText('')
    setMsgs((x) => [...x, { role: 'user', content: m }])
    setBusy(true)
    const put = (content: string) => setMsgs((x) => [...x.slice(0, -1), { role: 'assistant', content }])
    try {
      const r = await fetch(`/api/ai/chat/stream?today=${todayIso()}`, {
        method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: m }),
      })
      if (!r.ok || !r.body) throw new Error(r.status === 401 ? t('Signed out') : r.statusText)
      setMsgs((x) => [...x, { role: 'assistant', content: '' }])
      const rd = r.body.pipeThrough(new TextDecoderStream()).getReader()
      let acc = ''
      for (;;) {
        const { done, value } = await rd.read()
        if (done) break
        acc += value
        put(acc.replace(/<think>[\s\S]*?(<\/think>|$)/g, '').trimStart())
      }
    } catch (e: any) {
      setMsgs((x) => [...x, { role: 'assistant', content: `⚠️ ${e.message}` }])
    } finally {
      setBusy(false)
    }
  }
  const submit = (e: FormEvent) => { e.preventDefault(); send(text) }
  const clear = async () => { await api('/api/ai/chat', { method: 'DELETE' }); setMsgs([]) }

  if (status && !status.enabled) {
    return (
      <div className="px-6 pt-16 text-center">
        <div className="mx-auto mb-4 grid h-20 w-20 place-items-center rounded-full bg-[#F1EBFF] text-[#7C5CE0]"><Sparkles size={36} /></div>
        <h1 className="text-2xl font-black">{t('AI assistant is off')}</h1>
        <p className="mt-2 text-muted">{t('Connect Claude, OpenAI or another AI provider to get personal answers about your cycle.')}</p>
        <Link to="/profile" className="btn-primary mt-6">{t('Set up AI')}</Link>
      </div>
    )
  }

  return (
    <div className="flex min-h-[calc(100dvh-var(--nav-h))] flex-col">
      <header className="sticky top-0 z-10 flex items-center justify-between bg-canvas/95 px-5 pb-3 pt-4 backdrop-blur">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-black"><Sparkles className="text-[#7C5CE0]" /> {t('Ask Bloomery')}</h1>
          {status && <div className="text-xs text-muted">{status.local ? t('🔒 Runs locally') : t('☁️ Cloud')} · {status.model}</div>}
        </div>
        {msgs.length > 0 && <button onClick={clear} className="rounded-full p-2 text-muted hover:bg-pink-100" aria-label={t('Clear chat')}><Trash2 size={20} /></button>}
      </header>

      <div className="flex-1 space-y-3 px-4 pb-4">
        {msgs.length === 0 && (
          <div className="pt-6">
            <div className="card bg-gradient-to-br from-[#F4ECFF] to-[#FFE3EC] p-5 dark:from-[#2B2340] dark:to-[#3A2130]">
              <p className="font-bold">{t('Hi! I know your cycle history and logs, so you can ask me personal questions about your body, symptoms and predictions.')}</p>
              <p className="mt-2 text-xs text-muted">{t('I\'m not a doctor — for medical concerns please see a healthcare professional.')}</p>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(t(s))} className="rounded-full border border-line bg-card px-4 py-2 text-sm font-semibold hover:border-pink-300">{t(s)}</button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => m.content && (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] whitespace-pre-wrap rounded-3xl px-4 py-3 text-[15px] leading-relaxed ${m.role === 'user' ? 'rounded-br-lg bg-pink-500 text-white' : 'card rounded-bl-lg'}`}>
              {m.content}
            </div>
          </div>
        ))}
        {busy && (msgs.at(-1)?.role === 'user' || !msgs.at(-1)?.content) && (
          <div className="card inline-flex gap-1 rounded-3xl rounded-bl-lg px-4 py-4">
            {[0, 1, 2].map((i) => <span key={i} className="h-2 w-2 animate-bounce rounded-full bg-pink-300" style={{ animationDelay: `${i * 0.15}s` }} />)}
          </div>
        )}
        <div ref={end} />
      </div>

      <form onSubmit={submit} className="sticky bottom-[var(--nav-h)] bg-gradient-to-t from-canvas via-canvas to-transparent px-4 pb-3 pt-4">
        <div className="flex items-end gap-2 rounded-[1.75rem] bg-card p-2 pl-5 shadow-lg">
          <textarea rows={1} value={text} onChange={(e) => setText(e.target.value)} placeholder={t('Ask about your cycle…')}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(text) } }}
            className="max-h-32 flex-1 resize-none bg-transparent py-2 outline-none" />
          <button disabled={!text.trim() || busy} className="grid h-10 w-10 place-items-center rounded-full bg-pink-500 text-white disabled:opacity-40" aria-label={t('Send')}>
            <ArrowUp size={20} />
          </button>
        </div>
      </form>
    </div>
  )
}
