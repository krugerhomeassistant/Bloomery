import { useEffect, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { api, type User } from '../api'
import { useApp } from '../state'
import { Sheet } from './ui'
import { t } from '../i18n'

/** "My words": the user's own replacements for any word the app uses (whole words, any case). */
export default function Words({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, setUser } = useApp()
  const [rows, setRows] = useState<[string, string][]>([])
  const [busy, setBusy] = useState(false)
  useEffect(() => { if (open) setRows(user?.words?.length ? user.words : [['', '']]) }, [open, user?.words])
  const set = (i: number, j: 0 | 1, v: string) => setRows(rows.map((r, k) => (k === i ? (j ? [r[0], v] : [v, r[1]]) : r)) as [string, string][])
  const save = async () => {
    setBusy(true)
    try { setUser(await api<User>('/api/words', { method: 'PUT', body: { words: rows.filter(([a, b]) => a.trim() && b.trim()) }, today: false })); onClose() }
    finally { setBusy(false) }
  }
  return (
    <Sheet open={open} onClose={onClose} title={t('My words')}>
      <div className="space-y-3 px-5 pb-8">
        <p className="text-sm text-muted">{t('Swap any word Bloomery uses for your own, in every screen, message and notification. Whole words only, and capitals are kept.')}</p>
        {rows.map(([a, b], i) => (
          <div key={i} className="flex items-center gap-2">
            <input className="input min-w-0 flex-1" maxLength={40} placeholder={t('Instead of…')} value={a} onChange={(e) => set(i, 0, e.target.value)} />
            <span className="text-muted">→</span>
            <input className="input min-w-0 flex-1" maxLength={40} placeholder={t('Say…')} value={b} onChange={(e) => set(i, 1, e.target.value)} />
            <button className="rounded-full p-2 text-muted hover:bg-pink-100" aria-label={t('Delete')} onClick={() => setRows(rows.filter((_, k) => k !== i))}><Trash2 size={18} /></button>
          </div>
        ))}
        <button className="btn-ghost text-sm" onClick={() => setRows([...rows, ['', '']])}><Plus size={16} /> {t('Add a word')}</button>
        <button className="btn-primary w-full" disabled={busy} onClick={save}>{t('Save')}</button>
      </div>
    </Sheet>
  )
}
