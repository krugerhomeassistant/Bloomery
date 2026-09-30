import { useEffect, useState } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import { api } from '../api'
import { useApp } from '../state'
import { Sheet } from './ui'

type Cfg = { provider: string; base_url: string; model: string; has_key: boolean; key_hint: string; providers: Record<string, { base_url: string; model: string }> }

const PROVIDERS: { id: string; label: string; key?: string; models: string[]; note: string }[] = [
  { id: 'none', label: 'Off', models: [], note: 'Insights use built-in rules. Nothing leaves your server.' },
  { id: 'anthropic', label: 'Claude (Anthropic)', key: 'https://console.anthropic.com/settings/keys',
    models: ['claude-haiku-4-5-20251001', 'claude-sonnet-5-5', 'claude-opus-5-5'], note: 'Haiku is fast and cheapest; Sonnet/Opus give richer answers.' },
  { id: 'openai', label: 'OpenAI', key: 'https://platform.openai.com/api-keys', models: ['gpt-5-mini', 'gpt-5-nano', 'gpt-5'], note: '' },
  { id: 'openrouter', label: 'OpenRouter', key: 'https://openrouter.ai/keys', models: ['openrouter/auto'], note: 'One key for many models — use any model id from openrouter.ai/models.' },
  { id: 'ollama', label: 'Ollama (local)', models: ['llama3.2:3b', 'qwen3:8b'], note: 'Runs on your own hardware. Needs 3–4 GB free RAM.' },
  { id: 'custom', label: 'Other (OpenAI-compatible)', models: [], note: 'LM Studio, vLLM, LiteLLM… enter its /v1 URL.' },
]

export default function AiSettings({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { bump } = useApp()
  const [cfg, setCfg] = useState<Cfg | null>(null)
  const [err, setErr] = useState('')
  const [f, setF] = useState({ provider: 'none', model: '', base_url: '', api_key: '' })
  const [test, setTest] = useState<{ ok: boolean; msg: string } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    setTest(null)
    api<Cfg>('/api/ai/config', { today: false })
      .then((c) => { setCfg(c); setErr(''); setF({ provider: c.provider in c.providers ? c.provider : 'none', model: c.model, base_url: c.base_url, api_key: '' }) })
      .catch((e) => setErr(e.message))
  }, [open])

  const p = PROVIDERS.find((x) => x.id === f.provider) ?? PROVIDERS[0]
  const defaults = cfg?.providers[f.provider]
  const pick = (id: string) => { setF({ provider: id, model: '', base_url: '', api_key: '' }); setTest(null) }
  // blank model/url = provider default; blank key = keep saved key
  const body = () => ({ provider: f.provider, model: f.model.trim(), base_url: f.base_url.trim(), api_key: f.api_key.trim() || null })

  const run = async (kind: 'test' | 'save') => {
    setBusy(true)
    setTest(null)
    try {
      if (kind === 'test') {
        const r = await api<{ ok: boolean; reply?: string; error?: string }>('/api/ai/config/test', { body: body(), today: false })
        setTest({ ok: r.ok, msg: r.ok ? `Connected — model replied "${r.reply}"` : r.error! })
      } else {
        setCfg(await api<Cfg>('/api/ai/config', { method: 'PUT', body: body(), today: false }))
        bump()
        onClose()
      }
    } catch (e: any) {
      setTest({ ok: false, msg: e.message })
    } finally {
      setBusy(false)
    }
  }

  const sameProvider = cfg?.provider === f.provider
  return (
    <Sheet open={open} onClose={onClose} title="AI assistant">
      <div className="space-y-4 px-5 pb-8">
        {err ? <p className="text-muted">{err}</p> : !cfg ? <p className="text-muted">Loading…</p> : (
          <>
            <label className="block">
              <span className="mb-1 block text-sm font-bold text-muted">Provider</span>
              <select className="input" value={f.provider} onChange={(e) => pick(e.target.value)}>
                {PROVIDERS.map((x) => <option key={x.id} value={x.id}>{x.label}</option>)}
              </select>
              {p.note && <span className="mt-1 block text-xs text-muted">{p.note}</span>}
            </label>

            {f.provider !== 'none' && (
              <>
                {f.provider !== 'ollama' && (
                  <label className="block">
                    <span className="mb-1 flex justify-between text-sm font-bold text-muted">
                      API key {p.key && <a href={p.key} target="_blank" rel="noreferrer" className="text-pink-500">Get a key ↗</a>}
                    </span>
                    <input className="input" type="password" autoComplete="off" value={f.api_key}
                      placeholder={sameProvider && cfg.has_key ? `Saved key ····${cfg.key_hint} (leave blank to keep)` : 'Paste your API key'}
                      onChange={(e) => setF({ ...f, api_key: e.target.value })} />
                  </label>
                )}
                <label className="block">
                  <span className="mb-1 block text-sm font-bold text-muted">Model</span>
                  <input className="input" list="ai-models" value={f.model} placeholder={defaults?.model || 'model id'}
                    onChange={(e) => setF({ ...f, model: e.target.value })} />
                  <datalist id="ai-models">{p.models.map((m) => <option key={m} value={m} />)}</datalist>
                </label>
                <details open={f.provider === 'custom' || f.provider === 'ollama'}>
                  <summary className="cursor-pointer text-sm font-bold text-muted">Advanced</summary>
                  <label className="mt-2 block">
                    <span className="mb-1 block text-sm font-bold text-muted">Base URL</span>
                    <input className="input" value={f.base_url} placeholder={defaults?.base_url || 'http://host:port/v1'}
                      onChange={(e) => setF({ ...f, base_url: e.target.value })} />
                  </label>
                </details>
                {f.provider !== 'ollama' && (
                  <p className="rounded-2xl bg-pink-50 p-3 text-xs text-muted">
                    🔒 Your key is stored only on your server. With a cloud provider, a summary of your recent cycle data is sent to it when you use AI features.
                  </p>
                )}
              </>
            )}

            {test && (
              <div className={`flex gap-2 rounded-2xl p-3 text-sm ${test.ok ? 'bg-teal-50 text-teal-600' : 'bg-pink-50 text-pink-600'}`}>
                {test.ok ? <CheckCircle2 size={18} className="shrink-0" /> : <XCircle size={18} className="shrink-0" />}
                <span className="break-words">{test.msg}</span>
              </div>
            )}
            <div className="flex gap-3">
              {f.provider !== 'none' && <button className="btn-ghost flex-1" disabled={busy} onClick={() => run('test')}>Test</button>}
              <button className="btn-primary flex-1" disabled={busy} onClick={() => run('save')}>Save</button>
            </div>
          </>
        )}
      </div>
    </Sheet>
  )
}
