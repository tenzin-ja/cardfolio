import type { ReactNode } from 'react'
import charizard from '../../assets/sample-cards/charizard.webp'
import pikachu from '../../assets/sample-cards/pikachu.webp'
import gengar from '../../assets/sample-cards/gengar.webp'
import './auth.css'

type AuthLayoutProps = {
  children: ReactNode
}

// Login and registration share the same artwork, spacing, and responsive frame.
// Colors come from AppShell, so the layout follows the existing theme preference.
export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <section className="auth-layout" aria-label="Account access">
      <div className="auth-intro">
        <div className="auth-intro-copy">
          <h2>Your collection, together.</h2>
          <p>One place for the cards you collect.</p>
        </div>

        {/* Reuse the existing TCGdex sample artwork. These cards are decorative,
            so they don't add repeated card descriptions to the form's reading order. */}
        <div className="auth-card-display" aria-hidden="true">
          <img className="auth-card auth-card-pikachu" src={pikachu}
            width="600" height="825" alt="" />
          <img className="auth-card auth-card-charizard" src={charizard}
            width="600" height="825" alt="" />
          <img className="auth-card auth-card-gengar" src={gengar}
            width="600" height="825" alt="" />
        </div>
      </div>

      {/* Form content stays separate from the artwork and shared page layout. */}
      <div className="auth-content">{children}</div>
    </section>
  )
}
