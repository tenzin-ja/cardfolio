import { AppShell } from './components/AppShell'
import { CollectionPreview } from './components/CollectionPreview'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import './App.css'

// helps us update the value of Theme, and rerender the component if a switch occurs
import { useState, useEffect } from 'react'

//imports from appshell. defs used to check on whether values are valid
import type { Theme, AppPage } from './components/AppShell'

import {Routes,Route, useLocation, useNavigate} from 'react-router'
import {PageHeader} from './components/PageHeader'

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
  // Save the current preference whenever the theme changes.
  useEffect(() => {
    localStorage.setItem('cardfolio-theme', theme)
  }, [theme])


  return (
    <AppShell
    theme={theme}
    activePage={activePage}
    onThemeChange={setTheme}
    onNavigate={handleNavigate}
  >
      <Routes>
      {/* The root URL displays the collection preview. */}
      <Route path="/" element={<CollectionPreview />} />

      {/* Establish the search route before building its full interface. */}
      <Route
        path="/search"
        element={<PageHeader title="Find cards" />}
      />

      {/* Authentication screens share a layout; request handlers are connected separately. */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Give unknown URLs a clear result instead of an empty content area. */}
      <Route
        path="*"
        element={<PageHeader title="Page not found" />}
      />
    </Routes>
    </AppShell>
  )
}
export default App
