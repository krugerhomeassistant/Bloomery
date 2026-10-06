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

// The user's own word swaps ("period" -> "my time"), applied to every translated string. Whole words, any case.
let swaps: [RegExp, string][] = []
export function setWords(words: [string, string][]) {
  const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  swaps = [...words].sort((a, b) => b[0].length - a[0].length).map(([a, b]) => [new RegExp(`(?<![\\p{L}\\p{N}_{}])${esc(a)}(?![\\p{L}\\p{N}_{}])`, 'giu'), b])
}
export const swap = (s: string) => swaps.reduce((acc, [rx, b]) => acc.replace(rx, (m) => (m.length > 1 && m === m.toUpperCase() ? b.toUpperCase() : m[0] === m[0].toUpperCase() && m[0] !== m[0].toLowerCase() ? b[0].toUpperCase() + b.slice(1) : b)), s)

/** t(key, vars): key is the English text with {name} placeholders; a missing translation falls back to English. */
export function t(text: string, vars?: Record<string, string | number | null | undefined>): string {
  let s = (current === 'en' ? undefined : CATALOGS[current]?.[text]) ?? text
  if (swaps.length) s = swap(s)  // before filling placeholders, so typed names and notes stay as they are
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s
}
/** Marks a string for translation without translating it yet (module-level constants); render it with t(). */
export const N_ = (text: string) => text

export const plural = (n: number, one: string, many: string, vars?: Record<string, string | number | null | undefined>) => t(n === 1 ? one : many, { n, ...vars })

/** date-fns format in the active language. */
export const format = (d: Date | number | string, pattern: string) => dfFormat(d, pattern, { locale: current === 'af' ? dfAf : undefined })
export { CATALOGS }
