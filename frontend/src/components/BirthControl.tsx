import { useEffect, useState } from 'react'
import { api, iso } from '../api'
import { useApp } from '../state'
import { Sheet } from './ui'
import { t , N_ } from '../i18n'

type Cfg = { method: string; start?: string | null; pill_type?: string | null; expires?: string | null }
type Status = { emoji: string; title: string; text: string } | null

export const METHODS: [string, string][] = [
  ['none', N_('None / not tracking')], ['pill', N_('Pill')], ['ring', N_('Vaginal ring')], ['patch', N_('Patch')], ['injection', N_('Injection (e.g. Depo-Provera)')],
  ['iud_hormonal', N_('Hormonal IUD')], ['iud_copper', N_('Copper IUD')], ['implant', N_('Implant')], ['condom', N_('Condoms')], ['other', N_('Other')],
]
const START_LABEL: Record<string, string> = {
  pill: N_('First day of current pack'), ring: N_('Day this ring went in'), patch: N_('Day the first patch of this cycle went on'),
  injection: N_('Date of last injection'), iud_hormonal: N_('Date it was fitted'), iud_copper: N_('Date it was fitted'), implant: N_('Date it was fitted'),
}
const HORMONAL = ['pill', 'ring', 'patch', 'injection', 'iud_hormonal', 'implant']

export default function BirthControl({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { bump } = useApp()
  const [f, setF] = useState<Cfg>({ method: 'none' })
  const [st, setSt] = useState<Status>(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    if (open) { setErr(''); api<{ config: Cfg; status: Status }>('/api/contraception').then((r) => { setF(r.config); setSt(r.status) }) }
  }, [open])
  const save = async () => {
    setErr('')
    try {
      const r = await api<{ config: Cfg; status: Status }>('/api/contraception', { method: 'PUT', body: { ...f, start: f.start || null, expires: f.expires || null } })
      setSt(r.status); bump(); onClose()
    } catch (e: any) { setErr(e.message) }
  }
  const needsStart = f.method in START_LABEL

  return (
    <Sheet open={open} onClose={onClose} title={t('Birth control')}>
      <div className="space-y-4 px-5 pb-8">
        {st && <div className="flex gap-3 rounded-2xl bg-pink-50 p-3 text-sm"><span className="text-2xl">{st.emoji}</span><div><b>{st.title}</b><div className="text-muted">{st.text}</div></div></div>}
        <label className="block text-sm font-semibold">{t('Method')}
          <select className="input mt-1" value={f.method} onChange={(e) => setF({ method: e.target.value, start: f.start, pill_type: e.target.value === 'pill' ? f.pill_type ?? '21_7' : null })}>
            {METHODS.map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
          </select>
        </label>
        {f.method === 'pill' && (
          <label className="block text-sm font-semibold">{t('Pack type')}
            <select className="input mt-1" value={f.pill_type ?? '21_7'} onChange={(e) => setF({ ...f, pill_type: e.target.value })}>
              <option value="21_7">{t('21 active + 7-day break')}</option>
              <option value="24_4">{t('24 active + 4 inactive')}</option>
              <option value="28">{t('28 days, no break')}</option>
              <option value="pop">{t('Progestin-only (mini-pill)')}</option>
            </select>
          </label>
        )}
        {needsStart && f.pill_type !== 'pop' && (
          <label className="block text-sm font-semibold">{t(START_LABEL[f.method])}
            <input type="date" className="input mt-1" max={iso(new Date())} value={f.start ?? ''} onChange={(e) => setF({ ...f, start: e.target.value })} />
          </label>
        )}
        {['iud_hormonal', 'iud_copper', 'implant'].includes(f.method) && (
          <label className="block text-sm font-semibold">{t('Replace by (from your clinic or leaflet)')}
            <input type="date" className="input mt-1" value={f.expires ?? ''} onChange={(e) => setF({ ...f, expires: e.target.value })} />
          </label>
        )}
        <p className="text-xs text-muted">
          {HORMONAL.includes(f.method) ? t('Hormonal methods usually stop ovulation, so fertile-window predictions are hidden while this is set. Bleeds are still predicted. ') : ''}
          {t('Reminders arrive with your daily notifications (Profile → Daily reminders → Birth control reminders). Always follow your leaflet or clinician.')}
        </p>
        {err && <p className="text-sm font-bold text-pink-600">{err}</p>}
        <button className="btn-primary w-full" onClick={save}>{t('Save')}</button>
      </div>
    </Sheet>
  )
}
