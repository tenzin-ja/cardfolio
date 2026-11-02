import { AppShell } from './components/AppShell'
import { CollectionPreview } from './components/CollectionPreview'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import './App.css'


// helps us update the value of Theme, and rerender the component if a switch occurs
import { useState, useEffect } from 'react'

//imports from appshell. defs used to check on whether values are valid
import type { Theme, AppPage } from './components/AppShell'

import {Navigate, Routes, Route, useLocation, useNavigate} from 'react-router'
import {PageHeader} from './components/PageHeader'
import { getCurrentUser } from './api/auth'
import type { CurrentUser } from './api/auth'

function App() {
  
  const navigate = useNavigate()
  const {pathname} = useLocation()

  // Highlight the sidebar item that matches the current URL.
  // This also keeps the highlight correct when using Back or Forward.
  let activePage: AppPage | null = null

  if (pathname === '/'){
    activePage = 'collection'
  }else if (pathname === '/search'){
    activePage = 'search'
  }

  // Open the page selected in the sidebar
  function handleNavigate(page: AppPage){
    navigate(page === 'collection' ? '/' : '/search')
  }
  
  // Store the selected theme. Theme allows only 'light' or 'dark'.
  // savedTheme saves the chosen theme so refreshing doesn't reset. theme to be shown is now chosen from localstorage
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('cardfolio-theme')
    return savedTheme === 'dark' ? 'dark' : 'light'
  })
  // Keep the token here so changing pages doesn't discard the session.
  const [accessToken, setAccessToken] = useState<string | null>(null)
  
  // Store the account separately from the token used to authenticate requests.
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null)

  // These values control the sidebar's loading and error feedback.
  const [isAccountLoading, setIsAccountLoading] = useState(false)
  const [accountError, setAccountError] = useState<string | null>(null)

  useEffect(() => {
    localStorage.setItem('cardfolio-theme', theme)
  }, [theme])
  
  // Load account details after login supplies a token.
  useEffect(() => {
    if (!accessToken) return

    // Ignore a pending response if the token changes or App unmounts.
    let ignore = false

    async function loadAccount(token: string) {
      setIsAccountLoading(true)
      setAccountError(null)
      setCurrentUser(null)

      try {
        const user = await getCurrentUser(token)

        if (ignore) return

        // A rejected token ends the session. Existing route guards
        // will send the user back to login on protected pages.
        if (user === null) {
          setAccessToken(null)
          return
        }

        setCurrentUser(user)
      } catch (error) {
        if (ignore) return

        setAccountError(
          error instanceof Error
            ? error.message
            : 'Could not load your account. Please try again.',
        )
      } finally {
        if (!ignore) {
          setIsAccountLoading(false)
        }
      }
    }

    void loadAccount(accessToken)

    return () => {
      ignore = true
    }
  }, [accessToken])

  // Clear the current session and account feedback before returning to login.
  function handleLogout() {
    setAccessToken(null)
    setCurrentUser(null)
    setAccountError(null)
    setIsAccountLoading(false)

    navigate('/login', { replace: true })
  }


  return (
    <AppShell
    theme={theme}
    activePage={activePage}
    onThemeChange={setTheme}
    onNavigate={handleNavigate}
    isAuthenticated={Boolean(accessToken)}
    accountEmail={currentUser?.email}
    isAccountLoading={isAccountLoading}
    accountError={accountError}
    onLogout={handleLogout}
  >
      <Routes>
        {/* Require a session before displaying collection or search pages. */}
        <Route
          path="/"
          element={
            accessToken                           // Check whether a token exists.
              ? <CollectionPreview />             // If yes, show this component.
              : <Navigate to="/login" replace />  // Otherwise, redirect to login.
          }
        />

        <Route
          path="/search"
          element={
            accessToken
              ? <PageHeader title="Find cards" />
              : <Navigate to="/login" replace />
          }
        />

        <Route 
          path="/register"
          element = {<RegisterPage />}  
        />

        {/* Successful login passes its token into App's state setter. */}
        <Route
          path="/login"
          element={<LoginPage onLogin={setAccessToken} />}
        />
        
        {/* Show a message when the URL doesn't match an existing route. */}
        <Route
          path="*"
          element={<PageHeader title="Page not found" />}
        />

    </Routes>
    </AppShell>
  )
}
export default App
