import { useState } from 'react'
import type { SubmitEvent } from 'react'
import { useNavigate } from 'react-router'
import { login } from '../api/auth'
import { AuthLayout } from '../components/auth/AuthLayout'
import { LoginForm } from '../components/auth/LoginForm'

type LoginPageProps = {
  // App supplies this callback so we can pass the login token back to it.
  onLogin: (token: string) => void
}

// Connect the login form to the API and handle feedback and navigation.
export function LoginPage({ onLogin }: LoginPageProps) {
  const navigate = useNavigate()

  // These values control the form's loading state and error message.
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Read the credentials, request a token, and pass it to App on success.
  async function handleLogin(event: SubmitEvent<HTMLFormElement>) {
    // currentTarget is the submitted form. Read its fields before awaiting.
    const formData = new FormData(event.currentTarget)

    // Missing fields become empty strings. Trim the email, but preserve
    // the password exactly as entered, including any spaces.
    const email = String(formData.get('email') ?? '').trim()
    const password = String(formData.get('password') ?? '')

    // Clear any previous error and prevent another submission while waiting.
    setError(null)
    setIsSubmitting(true)

    try {
      const token = await login(email, password)

      // Give App the token before leaving the login page.
      onLogin(token)

      // Open the collection and replace this login entry in browser history.
      navigate('/', { replace: true })
    } catch (error) {
      // Use the helper's error message when available.
      // Other thrown values get a fallback message.
      setError(
        error instanceof Error
          ? error.message
          : 'Could not log in. Please try again.',
      )
    } finally {
      // End the loading state whether the request succeeds or fails.
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <AuthLayout>
        {/* The form displays the UI; this page supplies its behavior and status. */}
        <LoginForm
          onSubmit={handleLogin}
          isSubmitting={isSubmitting}
          error={error}
          onCreateAccount={() => navigate('/register')}
        />
      </AuthLayout>
    </div>
  )
}