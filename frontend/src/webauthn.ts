/** WebAuthn (passkeys) + Web Push helpers: base64url <-> bytes for the JSON the server speaks. */
import { api } from './api'

const toBytes = (s: string) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), (c) => c.charCodeAt(0))
const toB64 = (b: ArrayBuffer | null) => (b ? btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') : null)
const creds = (list: any[] = []) => list.map((c) => ({ ...c, id: toBytes(c.id) }))

export const passkeysSupported = () => window.isSecureContext && 'PublicKeyCredential' in window

/** Create a passkey on this device (Face ID / Touch ID / fingerprint / Windows Hello) and register it. */
export async function addPasskey(name: string) {
  const o = await api<any>('/api/auth/passkey/register/options', { method: 'POST', today: false })
  const cred = (await navigator.credentials.create({
    publicKey: { ...o, challenge: toBytes(o.challenge), user: { ...o.user, id: toBytes(o.user.id) }, excludeCredentials: creds(o.excludeCredentials) },
  })) as PublicKeyCredential
  const r = cred.response as AuthenticatorAttestationResponse
  return api('/api/auth/passkey/register', {
    today: false,
    body: { name, credential: { id: cred.id, rawId: toB64(cred.rawId), type: cred.type, authenticatorAttachment: cred.authenticatorAttachment, clientExtensionResults: {},
      response: { clientDataJSON: toB64(r.clientDataJSON), attestationObject: toB64(r.attestationObject), transports: r.getTransports?.() ?? [] } } },
  })
}

/** Ask this device's biometrics to unlock the app. */
export async function unlockWithPasskey() {
  const o = await api<any>('/api/auth/passkey/unlock/options', { method: 'POST', today: false })
  const cred = (await navigator.credentials.get({ publicKey: { ...o, challenge: toBytes(o.challenge), allowCredentials: creds(o.allowCredentials) } })) as PublicKeyCredential
  const r = cred.response as AuthenticatorAssertionResponse
  return api('/api/auth/passkey/unlock', {
    today: false,
    body: { credential: { id: cred.id, rawId: toB64(cred.rawId), type: cred.type, authenticatorAttachment: cred.authenticatorAttachment, clientExtensionResults: {},
      response: { clientDataJSON: toB64(r.clientDataJSON), authenticatorData: toB64(r.authenticatorData), signature: toB64(r.signature), userHandle: toB64(r.userHandle) } } },
  })
}

// ---------------------------------------------------------------- Web Push
export const pushSupported = () => window.isSecureContext && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
/** iPhone/iPad only allow push for apps added to the Home Screen. */
export const needsHomeScreen = () => /iPhone|iPad|iPod/.test(navigator.userAgent) && !matchMedia('(display-mode: standalone)').matches

export async function currentPushSubscription() {
  if (!pushSupported()) return null
  return (await navigator.serviceWorker.ready).pushManager.getSubscription()
}

export async function enablePush() {
  if ((await Notification.requestPermission()) !== 'granted') throw new Error('Notifications are blocked for Bloomery in your browser or phone settings.')
  const { public_key } = await api<{ public_key: string }>('/api/notifications/push', { today: false })
  const reg = await navigator.serviceWorker.ready
  const sub = (await reg.pushManager.getSubscription()) ?? (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: toBytes(public_key) }))
  return api('/api/notifications/push', { today: false, body: sub.toJSON() })
}

export async function disablePush() {
  const sub = await currentPushSubscription()
  if (!sub) return
  await api(`/api/notifications/push?endpoint=${encodeURIComponent(sub.endpoint)}`, { method: 'DELETE', today: false })
  await sub.unsubscribe()
}
