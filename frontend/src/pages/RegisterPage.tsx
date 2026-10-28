import { useState } from 'react'
import type { SubmitEvent } from 'react'
import { useNavigate } from 'react-router'
import { AuthLayout } from '../components/auth/AuthLayout'
import { RegisterForm } from '../components/auth/RegisterForm'

// The page handles navigation. The form receives request state separately,
// so its onSubmit handler can be connected without changing the shared layout.
export function RegisterPage() {
  const navigate = useNavigate()

  // These values control the form's existing loading and error displays.
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // waits for a submit event. upon an event
  // submits the form's email and password to create an account.
  async function handleRegister(event: SubmitEvent<HTMLFormElement>) {
    // Read the form before awaiting anything or disabling its fields.
    const formData = new FormData(event.currentTarget)
    const email = String(formData.get('email') ?? '').trim()
    const password = String(formData.get('password') ?? '')

    setError(null)
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      // The backend returns 201 when it successfully creates an account.
      if (response.status === 201) {
        navigate('/login')
        return
      }

      if (response.status === 409) {
        setError('An account with this email already exists.')
        return
      }

      setError(
        'Could not create your account. Check your details and try again.',
      )
    } catch {
      // Network failures reach catch; HTTP error responses are handled above.
      setError('Could not reach Cardfolio. Please try again.')
    } finally {
      // Always finish the loading state, including after an error.
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <AuthLayout>
        <RegisterForm
          onSubmit={handleRegister}
          isSubmitting={isSubmitting}
          error={error}
          onShowLogin={() => navigate('/login')}
        />
      </AuthLayout>
    </div>
  )
}