import type { ReactNode } from 'react'
import { Icon } from './Icon'

export type Theme = 'light' | 'dark'
export type AppPage = 'collection' | 'search'

type AppShellProps = {
  children: ReactNode
  theme: Theme
  activePage: AppPage
  // The parent owns state and routing; the shell reports which option was clicked.
  onThemeChange?: (theme: Theme) => void
  onNavigate?: (page: AppPage) => void
}

// Keep labels and icons together so desktop and mobile use the same navigation.
const navigation = [
  { page: 'collection', label: 'My collection', icon: 'cards' },
  { page: 'search', label: 'Find cards', icon: 'search' },
] as const

export function AppShell({
  children, theme, activePage, onThemeChange, onNavigate,
}: AppShellProps) {
  return (
    // Both themes share the same markup. This attribute selects the color tokens.
    <div className="app-shell" data-theme={theme}>
      <a className="skip-link" href="#main-content">Skip to content</a>

      <aside className="sidebar" aria-label="Application sidebar">
        <div className="brand" aria-label="Cardfolio">
          <Icon name="cards" className="brand-mark" />
          <span>Cardfolio<span className="brand-period">.</span></span>
        </div>

        {/* activePage marks the current view. Navigation stays disabled until
            the parent supplies a handler that actually changes the page. */}
        <nav className="primary-navigation" aria-label="Main navigation">
          {navigation.map(({ page, label, icon }) => (
            <button
              key={page}
              type="button"
              className="nav-link"
              aria-current={activePage === page ? 'page' : undefined}
              disabled={!onNavigate}
              title={!onNavigate ? 'Navigation is inactive in this design preview' : undefined}
              onClick={() => onNavigate?.(page)}
            >
              <Icon name={icon} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {/* aria-pressed identifies the selected option for assistive technology.
              The parent must update theme after receiving onThemeChange. */}
          <fieldset className="theme-picker">
            <legend>Appearance</legend>
            <div className="segmented-control">
              {(['light', 'dark'] as const).map((option) => (
                <button
                  key={option}
                  className="segment"
                  type="button"
                  aria-pressed={theme === option}
                  disabled={!onThemeChange}
                  title={!onThemeChange ? 'Theme switching is inactive in this design preview' : undefined}
                  onClick={() => onThemeChange?.(option)}
                >
                  <Icon name={option === 'light' ? 'sun' : 'moon'} />
                  <span>{option === 'light' ? 'Light' : 'Dark'}</span>
                </button>
              ))}
            </div>
          </fieldset>

          {/* Placeholder until the signed-in user's details are available. */}
          <div className="account-preview">
            <span className="account-avatar"><Icon name="user" /></span>
            <div>
              <p className="account-name">Your account</p>
              <p className="account-caption">Preview profile</p>
            </div>
          </div>
        </div>
      </aside>

      {/* The skip link targets this landmark. tabIndex lets keyboard users move
          focus here without adding the main element to the normal Tab order. */}
      <main id="main-content" className="main-content" tabIndex={-1}>
        {children}
      </main>
    </div>
  )
}
