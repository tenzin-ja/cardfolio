import type { ReactNode } from 'react'
import { Icon } from './Icon'

export type Theme = 'light' | 'dark'
export type AppPage = 'collection' | 'search'

type AppShellProps = {
  children: ReactNode
  theme: Theme
  // Unknown routes can display without highlighting a navigation item.
  activePage: AppPage | null
  // The parent owns state and routing; the shell reports which option was clicked.
  onThemeChange?: (theme: Theme) => void
  onNavigate?: (page: AppPage) => void
  // App supplies the session and account details; the shell only displays them.
  // An omitted session state means details are unavailable, rather than signed out.
  isAuthenticated?: boolean
  accountEmail?: string | null
  isAccountLoading?: boolean
  accountError?: string | null
  // App clears the session when this callback runs. No token handling lives here.
  onLogout?: () => void
}

// Keep labels and icons together so desktop and mobile use the same navigation.
const navigation = [
  { page: 'collection', label: 'My collection', icon: 'cards' },
  { page: 'search', label: 'Find cards', icon: 'search' },
] as const

export function AppShell({
  children, theme, activePage, onThemeChange, onNavigate,
  isAuthenticated, accountEmail, isAccountLoading = false, accountError, onLogout,
}: AppShellProps) {
  // Keep feedback tied to the supplied state, including while /auth/me is loading.
  let accountCaption = 'Account details unavailable.'
  if (isAuthenticated === false) {
    accountCaption = 'Not signed in'
  } else if (isAccountLoading) {
    accountCaption = 'Loading account…'
  } else if (accountError) {
    accountCaption = accountError
  } else if (accountEmail) {
    accountCaption = accountEmail
  }

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

          {/* Account details come from App. The live status announces loading
              and request feedback without moving keyboard focus. */}
          <div className="sidebar-account">
            <div className="account-summary">
              <span className="account-avatar"><Icon name="user" /></span>
              <div className="account-copy">
                <p className="account-name">Your account</p>
                <p className="account-caption" role="status">{accountCaption}</p>
              </div>
            </div>

            {/* Hide logout for guests; keep it disabled until a signed-in
                session and a real logout handler are supplied. */}
            {isAuthenticated !== false && (
              <button
                className="account-logout"
                type="button"
                disabled={!isAuthenticated || !onLogout}
                title={!onLogout ? 'Log out is unavailable' : undefined}
                onClick={onLogout}
              >
                <Icon name="logout" />
                <span>Log out</span>
              </button>
            )}
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
