import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { registerSW } from 'virtual:pwa-register'
import './index.css'
import App from './App'
import SharePage from './pages/SharePage'
import { AppProvider } from './state'

registerSW({ immediate: true })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProvider>
      {location.pathname.startsWith('/share/') ? <SharePage token={location.pathname.split('/')[2]} /> : <App />}
    </AppProvider>
  </StrictMode>,
)
