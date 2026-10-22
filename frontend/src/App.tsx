import { AppShell } from './components/AppShell'
import { CollectionPreview } from './components/CollectionPreview'
import './App.css'

function App() {
  // These fixed values let us review the layout before connecting behavior.
  // Replace them with theme and routing state, then pass onThemeChange and
  // onNavigate. The shell enables each control when its handler is provided.
  return (
    <AppShell theme="light" activePage="collection">
      {/* Replace this sample page with route content as real pages are built. */}
      <CollectionPreview />
    </AppShell>
  )
}

export default App
