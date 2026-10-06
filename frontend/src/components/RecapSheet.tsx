import { useEffect, useState } from 'react'
import { parseISO } from 'date-fns'
import { format, t } from '../i18n'
import { RefreshCw, Sparkles } from 'lucide-react'
import { api } from '../api'
import { Sheet } from './ui'

type Recap = { start: string; length: number | null; complete: boolean; source: 'ai' | 'rules'; content: string; error?: string }

/** AI (or rule-based) recap of the cycle starting on `start`. */
export default function RecapSheet({ start, onClose }: { start: string | null; onClose: () => void }) {
  const [r, setR] = useState<Recap | null>(null)
  const [busy, setBusy] = useState(false)
  const load = async (refresh = false) => {
    if (!start) return
    setBusy(true)
    try { setR(await api<Recap>(`/api/ai/recap?start=${start}${refresh ? '&refresh=true' : ''}`)) }
    catch (e: any) { setR({ start, length: null, complete: false, source: 'rules', content: e.message }) }
    finally { setBusy(false) }
  }
  useEffect(() => { setR(null); load() }, [start]) // eslint-disable-line react-hooks/exhaustive-deps

  const title = start && t('Cycle from {date}', { date: format(parseISO(start), 'MMM d') }) + (r?.length ? ` · ${t('{n} days', { n: r.length })}` : r && !r.complete ? ` · ${t('so far')}` : '')
  return (
    <Sheet open={!!start} onClose={onClose} title={<span className="flex items-center gap-2"><Sparkles size={20} className="text-[#7C5CE0]" />{title}</span>}>
      <div className="px-5 pb-8">
        {!r ? (
          <p className="flex items-center gap-2 text-muted"><RefreshCw size={16} className="animate-spin" /> {t('Writing your recap…')}</p>
        ) : (
          <>
            <p className="whitespace-pre-wrap leading-relaxed">{r.content}</p>
            {r.error && <p className="mt-3 text-xs text-muted">{t('AI unavailable, showing the basic summary (')}{r.error})</p>}
            {r.source === 'rules' && !r.error && <p className="mt-4 text-xs text-muted">{t('Turn on the AI assistant in Profile for a detailed, personal recap.')}</p>}
            {r.source === 'ai' && (
              <button className="btn-ghost mt-5 text-sm" disabled={busy} onClick={() => load(true)}>
                <RefreshCw size={16} className={busy ? 'animate-spin' : ''} /> {t('Rewrite')}
              </button>
            )}
          </>
        )}
        <p className="mt-6 text-xs text-muted">{t('Based on your own logs. Not medical advice.')}</p>
      </div>
    </Sheet>
  )
}
