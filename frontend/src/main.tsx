import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

import { BrowserRouter } from 'react-router'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
  {/* Tracks the current URL so Routes can show the matching page. */}
    <BrowserRouter>
    <App />
    </BrowserRouter>
  </StrictMode>,
)
