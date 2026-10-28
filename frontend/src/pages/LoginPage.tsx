import { useNavigate } from 'react-router'
import { AuthLayout } from '../components/auth/AuthLayout'
import { LoginForm } from '../components/auth/LoginForm'
import type { LoginFormProps } from '../components/auth/LoginForm'

// Keep the page composition simple. A parent can pass the request handler,
// loading state, and errors once authentication is connected.
export function LoginPage(props: LoginFormProps) {
  // Supply screen navigation here while leaving login requests to the parent.
  const navigate = useNavigate()

  return (
    <div className="auth-page">
      <AuthLayout>
        <LoginForm
          {...props}
          onCreateAccount={props.onCreateAccount ?? (() => navigate('/register'))}
        />
      </AuthLayout>
    </div>
  )
}
