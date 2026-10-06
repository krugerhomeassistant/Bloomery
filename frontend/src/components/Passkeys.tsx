import { useEffect, useState } from 'react'
import { ScanFace, Trash2 } from 'lucide-react'
import { api, type User } from '../api'
import { useApp } from '../state'
import { addPasskey, passkeysSupported } from '../webauthn'
import { t } from '../i18n'

type Key = { id: string; name: string; created: string; rp_id: string }
const deviceName = () => (/iPhone/.test(navigator.userAgent) ? 'iPhone' : /iPad/.test(navigator.userAgent) ? 'iPad' : /Android/.test(navigator.userAgent) ? 'Android phone' : /Mac/.test(navigator.userAgent) ? 'Mac' : /Windows/.test(navigator.userAgent) ? 'Windows PC' : 'This device')

/** Face ID / fingerprint unlock devices (WebAuthn passkeys), shown in the App lock sheet. */
export default function Passkeys() {
  const { setUser } = useApp()
  const [keys, setKeys] = useState<Key[]>([])
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => { api<Key[]>('/api/auth/passkey', { today: false }).then(setKeys).catch(() => {}) }, [])
  const done = async (k: Key[]) => { setKeys(k); setUser(await api<User>('/api/auth/me', { today: false })) }
  const add = async () => {
    setBusy(true); setErr('')
    try { await done(await addPasskey(deviceName()) as Key[]) }
    catch (e: any) { setErr(e.name === 'NotAllowedError' ? t('Cancelled.') : e.name === 'InvalidStateError' ? t('This device is already added.') : e.message) }
    finally { setBusy(false) }
  }
  const here = keys.filter((k) => k.rp_id === location.hostname)

  return (
    <div className="space-y-2 border-t border-line pt-4">
      <div className="flex items-center gap-2 font-bold"><ScanFace size={18} className="text-pink-500" /> {t('Face ID / fingerprint')}</div>
      {!passkeysSupported() ? (
        <p className="text-xs text-muted">{t('Needs Bloomery to be opened over HTTPS.')}</p>
      ) : (
        <>
          <p className="text-xs text-muted">{t('Unlock with your face or finger instead of typing the PIN. The PIN still works as a fallback.')}</p>
          {here.map((k) => (
            <div key={k.id} className="flex items-center justify-between rounded-2xl bg-pink-50 px-3 py-2 text-sm">
              <span>{k.name}</span>
              <button className="rounded-full p-1.5 text-muted hover:bg-pink-100" aria-label={`Remove ${k.name}`}
                onClick={async () => done(await api<Key[]>(`/api/auth/passkey/${k.id}`, { method: 'DELETE', today: false }))}><Trash2 size={16} /></button>
            </div>
          ))}
          <button type="button" className="btn-ghost w-full text-sm" disabled={busy} onClick={add}>{busy ? t('Waiting for your device…') : t('Add this device')}</button>
          {err && <p className="text-sm font-bold text-pink-600">{err}</p>}
        </>
      )}
    </div>
  )
}
