import { format as dfFormat } from 'date-fns'
import { af as dfAf } from 'date-fns/locale/af'
import { STRINGS as AF } from './locales/af'

export const LANGS = { en: 'English', af: 'Afrikaans' } as const
export type Lang = keyof typeof LANGS

const CATALOGS: Record<string, Record<string, string>> = { af: AF }
const stored = () => { try { return localStorage.getItem('lang') } catch { return null } }
export const detectLang = (): Lang => {
  const s = stored()
  if (s === 'en' || s === 'af') return s
  return navigator.language?.toLowerCase().startsWith('af') ? 'af' : 'en'
}

let current: Lang = detectLang()
export const getLang = () => current
export function setLang(l: Lang) {
  current = l
  document.documentElement.lang = l
  try { localStorage.setItem('lang', l) } catch {}
}
setLang(current)

/** t(key, vars): key is the English text with {name} placeholders; a missing translation falls back to English. */
export function t(text: string, vars?: Record<string, string | number | null | undefined>): string {
  const s = (current === 'en' ? undefined : CATALOGS[current]?.[text]) ?? text
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s
}
/** Marks a string for translation without translating it yet (module-level constants); render it with t(). */
export const N_ = (text: string) => text

export const plural = (n: number, one: string, many: string, vars?: Record<string, string | number | null | undefined>) => t(n === 1 ? one : many, { n, ...vars })

/** date-fns format in the active language. */
export const format = (d: Date | number | string, pattern: string) => dfFormat(d, pattern, { locale: current === 'af' ? dfAf : undefined })
export { CATALOGS }
