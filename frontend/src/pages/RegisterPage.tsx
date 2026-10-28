import { useNavigate } from 'react-router'
import { AuthLayout } from '../components/auth/AuthLayout'
import { RegisterForm } from '../components/auth/RegisterForm'
import type { RegisterFormProps } from '../components/auth/RegisterForm'

// The page handles navigation. The form receives request state separately,
// so its onSubmit handler can be connected without changing the shared layout.
export function RegisterPage(props: RegisterFormProps) {
  const navigate = useNavigate()

  return (
    <div className="auth-page">
      <AuthLayout>
        <RegisterForm
          {...props}
          onShowLogin={props.onShowLogin ?? (() => navigate('/login'))}
        />
      </AuthLayout>
    </div>
  )
}
