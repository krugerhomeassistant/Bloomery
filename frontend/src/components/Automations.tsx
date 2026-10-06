import { useState } from 'react'
import { api } from '../api'
import { useFetch } from '../state'

/** API key for quick logging from Siri Shortcuts, Home Assistant actions, NFC tags and scripts. */
export default function Automations() {
  const tok = useFetch<{ token: string | null }>('/api/tokens/api')
  const [shown, setShown] = useState(false)
  const key = tok.data?.token
  const act = async (method: 'POST' | 'DELETE') => {
    tok.setData(await api<{ token: string | null }>('/api/tokens/api', { method, body: method === 'POST' ? {} : undefined, today: false }))
    setShown(method === 'POST')
  }
  const base = `${location.origin}/api/quick`
  const Code = ({ children }: { children: string }) => <code className="block select-all break-all rounded-xl bg-pink-50 p-2 font-mono text-[11px] text-ink">{children}</code>

  return (
    <div className="space-y-3 px-4 py-4 text-sm">
      <p className="text-muted">Log from a Siri Shortcut, Home Assistant, an NFC tag or a script with an API key. The key can only <b>add</b> logs; it can't read or delete anything.</p>
      {!key ? (
        <button className="btn-ghost px-4 py-2 text-sm" onClick={() => act('POST')}>Create API key</button>
      ) : (
        <>
          <div className="font-bold">Your API key</div>
          {shown ? <Code>{key}</Code> : <button className="btn-ghost w-full text-sm" onClick={() => setShown(true)}>Show key</button>}
          <div className="flex flex-wrap gap-2">
            {window.isSecureContext && navigator.clipboard && <button className="btn-primary px-4 py-2 text-sm" onClick={() => navigator.clipboard.writeText(key)}>Copy key</button>}
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => act('POST')}>New key</button>
            <button className="btn-ghost px-4 py-2 text-sm" onClick={() => act('DELETE')}>Turn off</button>
          </div>

          <details className="rounded-2xl bg-pink-50/60 p-3">
            <summary className="cursor-pointer font-bold">Siri Shortcut: "Hey Siri, my period started"</summary>
            <ol className="mt-2 list-decimal space-y-1.5 pl-5 text-muted">
              <li>Shortcuts app → <b>+</b> → add the action <b>Get Contents of URL</b> with this URL:<Code>{`${base}/period-start`}</Code></li>
              <li>Tap ▸: Method <b>POST</b>, add header <b>Authorization</b> with value <b>Bearer</b> + space + your key.</li>
              <li>Name the shortcut <b>My period started</b>. Say "Hey Siri, my period started".</li>
            </ol>
          </details>
          <details className="rounded-2xl bg-pink-50/60 p-3">
            <summary className="cursor-pointer font-bold">Siri Shortcut: log symptoms</summary>
            <ol className="mt-2 list-decimal space-y-1.5 pl-5 text-muted">
              <li>Add <b>Choose from Menu</b> (or <b>Ask for Input</b>) with options like Cramps, Headache, Bloating.</li>
              <li>Add <b>Get Contents of URL</b>:<Code>{`${base}/log`}</Code></li>
              <li>Method <b>POST</b>, same <b>Authorization</b> header, Request Body <b>JSON</b>: field <b>tags</b> (Array) containing the chosen item. Optional fields: <b>flow</b>, <b>temperature</b>, <b>note</b>.</li>
            </ol>
          </details>
          <details className="rounded-2xl bg-pink-50/60 p-3">
            <summary className="cursor-pointer font-bold">Home Assistant and scripts</summary>
            <p className="mt-2 text-muted">Home Assistant: Bloomery integration → <b>Configure</b> → paste the key, then use the <b>Log period start</b> and <b>Log</b> actions. Anything else:</p>
            <Code>{`curl -X POST ${base}/log -H "Authorization: Bearer YOUR_KEY" -H "Content-Type: application/json" -d '{"tags": ["cramps", "mood:sad"]}'`}</Code>
            <p className="mt-2 text-muted">Names work in any case (Cramps, cramps, mood:sad). Days default to today; send <b>day</b> (YYYY-MM-DD) or <b>tz</b> to change that.</p>
          </details>
        </>
      )}
    </div>
  )
}
