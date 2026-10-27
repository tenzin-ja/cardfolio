import { AuthLayout } from '../components/auth/AuthLayout'
import { LoginForm } from '../components/auth/LoginForm'
import type { LoginFormProps } from '../components/auth/LoginForm'

// Keep the page composition simple. A parent can pass the request handler,
// loading state, and errors once authentication is connected.
export function LoginPage(props: LoginFormProps) {
  return (
    <div className="auth-page">
      <AuthLayout>
        <LoginForm {...props} />
      </AuthLayout>
    </div>
  )
}
