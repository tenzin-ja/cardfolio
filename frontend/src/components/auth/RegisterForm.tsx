import { useId } from 'react'
import type { SubmitEvent, SubmitEventHandler } from 'react'

export type RegisterFormProps = {
  // The parent supplies the registration request and reports its loading/error state.
  onSubmit?: SubmitEventHandler<HTMLFormElement>
  isSubmitting?: boolean
  error?: string | null
  onShowLogin?: () => void
}

export function RegisterForm({
  onSubmit,
  isSubmitting = false,
  error = null,
  onShowLogin,
}: RegisterFormProps) {
  const formId = useId()
  const emailId = formId + '-email'
  const passwordId = formId + '-password'
  const errorId = formId + '-error'
  const previewId = formId + '-preview'

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    // Keep credentials out of a native form URL. Reading the fields and sending
    // them to the backend belongs to the handler supplied by the parent.
    event.preventDefault()
    if (isSubmitting || !onSubmit) return
    onSubmit(event)
  }

  return (
    <div className="auth-form">
      <header className="auth-heading">
        <h1>Create an account</h1>
        <p>Make a home for your card collection.</p>
      </header>

      <form
        onSubmit={handleSubmit}
        aria-busy={isSubmitting}
        aria-describedby={error ? errorId : undefined}
      >
        {/* The request handler can supply errors such as an already-registered email. */}
        {error && <p id={errorId} className="auth-error" role="alert">{error}</p>}

        <fieldset className="auth-fields" disabled={isSubmitting}>
          <legend className="sr-only">Registration details</legend>
          <div className="auth-field">
            <label htmlFor={emailId}>Email address</label>
            <input
              id={emailId}
              name="email"
              type="email"
              autoComplete="username"
              placeholder="you@example.com" /* taste-skill-ignore: Email-format hint, not account data. */
              maxLength={320}
              autoCapitalize="none"
              spellCheck={false}
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor={passwordId}>Password</label>
            <input
              id={passwordId}
              name="password"
              type="password"
              autoComplete="new-password"
              placeholder="Choose a password"
              minLength={8}
              maxLength={128}
              required
            />
          </div>
        </fieldset>

        <button
          className="button button-primary auth-submit"
          type="submit"
          disabled={!onSubmit || isSubmitting}
          aria-describedby={!onSubmit ? previewId : undefined}
        >
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </button>

        {!onSubmit && (
          <p id={previewId} className="auth-preview-note">
            Registration is unavailable in this UI preview.
          </p>
        )}
      </form>

      <p className="auth-account-prompt">
        Already have an account?{' '}
        <button
          className="auth-text-action"
          type="button"
          onClick={onShowLogin}
          disabled={!onShowLogin || isSubmitting}
        >
          Log in
        </button>
      </p>
    </div>
  )
}
