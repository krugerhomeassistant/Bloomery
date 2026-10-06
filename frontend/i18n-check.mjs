// Lists strings passed to t() / N_() in src/ that src/locales/af.ts doesn't translate yet; exits 1 if any are missing.
// `node i18n-check.mjs --dump` prints the missing English strings as JSON (for translators).
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const walk = (d) => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : [join(d, f)]))
const keys = new Set()
for (const f of walk('src').filter((f) => /\.tsx?$/.test(f) && !f.includes('locales'))) {
  const re = /(?<![\w.])(?:t|N_)\(\s*('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")/g
  for (const m of readFileSync(f, 'utf8').matchAll(re)) keys.add(Function(`return ${m[1]}`)())
}
const af = readFileSync('src/locales/af.ts', 'utf8')
const have = new Set([...af.matchAll(/^\s*("(?:[^"\\]|\\.)*"):/gm)].map((m) => JSON.parse(m[1])))
const ph = (s) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join()
const bad = [...af.matchAll(/^\s*("(?:[^"\\]|\\.)*"):\s*("(?:[^"\\]|\\.)*"),/gm)].filter((m) => ph(JSON.parse(m[1])) !== ph(JSON.parse(m[2]))).map((m) => JSON.parse(m[1]))
if (bad.length) { console.error('placeholder mismatch:\n  ' + bad.join('\n  ')); process.exit(1) }
const missing = [...keys].filter((k) => k.trim() && !have.has(k)).sort()
if (process.argv.includes('--dump')) console.log(JSON.stringify(missing, null, 1))
else if (missing.length) { console.error(`${missing.length} strings missing from src/locales/af.ts:\n` + missing.map((k) => '  ' + k).join('\n')) }
else console.log(`i18n: ${keys.size} strings, all translated`)
process.exit(missing.length ? 1 : 0)
