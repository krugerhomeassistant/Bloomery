import { useState } from 'react'
import { parseISO } from 'date-fns'
import { format, N_, t } from '../i18n'
import { ArrowLeft, Printer } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useApp, useFetch } from '../state'
import { LineChart, Logo, Spinner } from '../components/ui'
import { CycleTrend, SymptomMap, type Heatmap } from '../components/InsightCharts'

type Cycle = { start: string; length: number | null; days_so_far: number | null; period_length: number; heavy_days: number; spotting_days: number; ovulation: string; ovulation_confirmed: boolean; top: string[] }
type Report = {
  generated: string; since: string; months: number
  patient: { name: string; age: number | null; goal: string; life_stage: string; pregnancy: { week: number; day: number; due: string } | null }
  summary: { cycles: number; avg_cycle: number | null; min_cycle: number | null; max_cycle: number | null; sd_cycle: number | null; avg_period: number | null; last_period: string | null; next_period: string | null; regularity: string; luteal: number; bbt_confirmed: number }
  cycles: Cycle[]
  flags: { level: string; title: string; text: string }[]
  symptoms: { label: string; days: number }[]
  patterns: { label: string; phase: string; share: number }[]
  heatmap: Heatmap
  temperature: { date: string; value: number }[]
  pill: { taken: number; missed: number } | null
  tests: { date: string; test: string; result: string }[]
  notes: { date: string; text: string }[]
}
const d = (iso: string | null) => (iso ? format(parseISO(iso), 'd MMM yyyy') : '—')
const GOAL: Record<string, string> = { track: N_('Tracking cycle'), conceive: N_('Trying to conceive'), avoid: N_('Avoiding pregnancy (fertility awareness)') }
const PHASE: Record<string, string> = { menstrual: N_('during period'), follicular: N_('after period'), fertile: N_('around ovulation'), luteal: N_('before period') }

/** Printable summary for a GP / gynaecologist. "Save as PDF" from the print dialog makes the PDF. */
export default function Report() {
  const nav = useNavigate()
  const { catalog, user } = useApp()
  const [months, setMonths] = useState(6)
  const [notes, setNotes] = useState(false)
  const r = useFetch<Report>(`/api/report?months=${months}&notes=${notes}`, [months, notes]).data
  const emoji = (tag: string) => { const [c, i] = tag.split(':'); return catalog?.categories.find((x) => x.id === c)?.items.find((x) => x.id === i)?.emoji ?? '•' }
  const F = user?.temp_unit === 'F'
  if (!r) return <Spinner />
  const s = r.summary

  return (
    <div className="mx-auto max-w-3xl px-4 pb-10 pt-4 text-[15px] print:p-0 print:text-[12px]">
      <div className="no-print mb-4 flex flex-wrap items-center gap-2">
        <button className="rounded-full p-2 hover:bg-pink-100" onClick={() => nav(-1)} aria-label={t('Back')}><ArrowLeft /></button>
        <select className="input w-auto py-2" value={months} onChange={(e) => setMonths(+e.target.value)} aria-label={t('Period covered')}>
          {[3, 6, 12, 24].map((m) => <option key={m} value={m}>{t('Last')} {m} {t('months')}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm font-semibold"><input type="checkbox" className="h-4 w-4 accent-pink-500" checked={notes} onChange={(e) => setNotes(e.target.checked)} />{t('Include my notes')}</label>
        <button className="btn-primary ml-auto px-5 py-2.5 text-sm" onClick={() => print()}><Printer size={18} /> {t('Print / Save PDF')}</button>
        <p className="w-full text-xs text-muted">{t('Sex and activity logs are never included. Choose "Save as PDF" in the print dialog to keep a file.')}</p>
      </div>

      <header className="flex items-start justify-between border-b-2 border-pink-500 pb-3">
        <div>
          <h1 className="text-2xl font-black">{t('Menstrual cycle summary')}</h1>
          <div className="text-muted">{r.patient.name}{r.patient.age ? `, ${t('{n} years', { n: r.patient.age })}` : ''} · {t(GOAL[r.patient.goal] ?? r.patient.goal)}{r.patient.life_stage !== 'cycle' ? ` · ${t(r.patient.life_stage)}` : ''}</div>
          <div className="text-sm text-muted">{d(r.since)} {t('to')} {d(r.generated)} {t('· generated')} {d(r.generated)}</div>
        </div>
        <div className="flex items-center gap-2 text-sm font-bold text-pink-500"><Logo size={28} /> {t('Bloomery')}</div>
      </header>

      {r.patient.pregnancy && (
        <p className="mt-3 rounded-2xl bg-pink-50 p-3 font-semibold">{t('Pregnant:')} {r.patient.pregnancy.week} {t('weeks')} {r.patient.pregnancy.day} {t('days, due')} {d(r.patient.pregnancy.due)} {t('(from last menstrual period).')}</p>
      )}

      <section className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 print:grid-cols-4">
        <Fact k={t('Cycle length')} v={s.avg_cycle ? t('{n} d', { n: s.avg_cycle }) : '—'} sub={s.min_cycle ? t('range {a}–{b} d', { a: s.min_cycle, b: s.max_cycle }) + (s.sd_cycle !== null ? `, SD ${s.sd_cycle}` : '') : t('{n} complete cycles', { n: s.cycles })} />
        <Fact k={t('Period length')} v={s.avg_period ? t('{n} d', { n: s.avg_period }) : '—'} sub={t('average')} />
        <Fact k={t('Last period')} v={d(s.last_period)} sub={s.next_period ? t('next expected {d}', { d: d(s.next_period) }) : ''} />
        <Fact k={t('Regularity')} v={s.regularity === 'unknown' ? '—' : t(s.regularity)} sub={`${t('{n} complete cycles', { n: s.cycles })} · ${t('luteal {n} d', { n: s.luteal })}`} />
      </section>

      {r.flags.length > 0 && (
        <Section title={t('Flagged for discussion')}>
          <ul className="list-disc space-y-1 pl-5">{r.flags.map((f) => <li key={f.title}><b>{f.title}.</b> {f.text}</li>)}</ul>
        </Section>
      )}

      <Section title={t('Cycles')}>
        <div className="-mx-1 overflow-x-auto"><table className="w-full min-w-[34rem] text-left text-sm print:min-w-0 print:text-[11px] [&_td]:px-1 [&_td]:align-top [&_th]:px-1 [&_th]:align-bottom">
          <thead className="text-xs uppercase text-muted"><tr><th className="py-1">{t('Start')}</th><th>{t('Length')}</th><th>{t('Period')}</th><th>{t('Heavy days')}</th><th>{t('Spotting*')}</th><th>{t('Ovulation')}</th><th>{t('Most logged')}</th></tr></thead>
          <tbody className="divide-y divide-line">
            {r.cycles.map((c) => (
              <tr key={c.start}>
                <td className="whitespace-nowrap py-1.5">{d(c.start)}</td>
                <td>{c.length ? t('{n} d', { n: c.length }) : t('{n} d so far', { n: c.days_so_far })}</td>
                <td>{t('{n} d', { n: c.period_length })}</td>
                <td>{c.heavy_days || '—'}</td>
                <td>{c.spotting_days || '—'}</td>
                <td className="whitespace-nowrap">{format(parseISO(c.ovulation), 'd MMM')} {c.ovulation_confirmed ? t('(BBT)') : t('(est.)')}</td>
                <td className="text-muted">{c.top.join(', ') || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table></div>
        <p className="mt-1 text-xs text-muted">{t('*Spotting outside the period. Ovulation is estimated from cycle length unless confirmed by a sustained temperature rise (BBT,')} {s.bbt_confirmed} {t('cycles).')}</p>
      </Section>

      <Section title={t('Cycle length over time')}><div className="print:max-w-md"><CycleTrend history={[...r.cycles]} /></div></Section>

      {(r.symptoms.length > 0 || r.patterns.length > 0) && (
        <Section title={t('Symptoms and mood')}>
          {r.symptoms.length > 0 && <p><b>{t('Days logged:')}</b> {r.symptoms.map((x) => `${x.label} (${x.days})`).join(', ')}.</p>}
          {r.patterns.length > 0 && <p className="mt-1"><b>{t('Recurring patterns:')}</b> {r.patterns.map((p) => `${p.label} ${t(PHASE[p.phase] ?? p.phase)} (${t('{n}% of occurrences', { n: Math.round(p.share * 100) })})`).join('; ')}.</p>}
          {r.heatmap.rows.length > 0 && <div className="mt-3"><SymptomMap map={r.heatmap} emoji={emoji} /></div>}
        </Section>
      )}

      {r.temperature.length > 1 && (
        <Section title={t('Waking temperature ({u}; basal or wrist)', { u: F ? '°F' : '°C' })}>
          <LineChart color="#22ADA5" unit={F ? '°F' : '°C'} points={r.temperature.map((p) => ({ ...p, value: F ? p.value * 9 / 5 + 32 : p.value }))} />
        </Section>
      )}

      {(r.pill || r.tests.length > 0) && (
        <Section title={t('Contraception and tests')}>
          {r.pill && <p>{t('Pill: taken on')} {r.pill.taken} {t('logged days,')} <b>{t('missed')} {r.pill.missed}</b>.</p>}
          {r.tests.map((x) => <p key={x.date + x.test}>{d(x.date)}: {x.test} {x.result}</p>)}
        </Section>
      )}

      {r.notes.length > 0 && (
        <Section title={t('Notes')}>
          <ul className="space-y-1">{r.notes.map((n) => <li key={n.date}><span className="text-muted">{d(n.date)}:</span> {n.text}</li>)}</ul>
        </Section>
      )}

      <p className="mt-6 text-xs text-muted">{t('Self-reported data from the Bloomery cycle tracker. Predictions and ovulation dates are estimates, not a diagnosis.')}</p>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="card mt-4 p-4 print:mt-3 print:rounded-xl print:p-3"><h2 className="mb-2 font-extrabold text-pink-600">{title}</h2>{children}</section>
}

function Fact({ k, v, sub }: { k: string; v: string; sub: string }) {
  return (
    <div className="card p-3">
      <div className="text-[11px] font-extrabold uppercase text-muted">{k}</div>
      <div className="text-lg font-black first-letter:uppercase">{v}</div>
      <div className="text-xs text-muted">{sub}</div>
    </div>
  )
}
