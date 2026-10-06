// Web Push handlers, imported into the generated service worker (vite.config.ts → workbox.importScripts).
self.addEventListener('push', (event) => {
  const d = event.data ? event.data.json() : {}
  event.waitUntil(self.registration.showNotification(d.title || 'Bloomery', {
    body: d.body || '', icon: '/icon-192.png', badge: '/icon-192.png', tag: 'bloomery-daily', data: { url: d.url || '/' },
  }))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wins) => {
    const w = wins.find((c) => 'focus' in c)
    return w ? w.focus() : self.clients.openWindow(event.notification.data.url)
  }))
})
