import { useId } from 'react'
// Use React's submit-specific types for the event and its callback.
import type { SubmitEvent, SubmitEventHandler } from 'react'

//defines the functions and values that loginform can recieve from another component
export type LoginFormProps = {
  // The parent will supply the login request handler and its result state.
  onSubmit?: SubmitEventHandler<HTMLFormElement>
  isSubmitting?: boolean
  error?: string | null
  onCreateAccount?: () => void
}

export function LoginForm({
  onSubmit,
  isSubmitting = false,
  error = null,
  onCreateAccount,
}: LoginFormProps) {
  // Unique IDs keep field labels and feedback connected even if forms are reused.
  const formId = useId()
  const emailId = formId + '-email'
  const passwordId = formId + '-password'
  const errorId = formId + '-error'
  const previewId = formId + '-preview'

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    // Always prevent native form navigation, including in the unconnected preview.
    // The parent handles reading the fields, requests, and session changes.
    event.preventDefault()
    if (isSubmitting || !onSubmit) return
    onSubmit(event)
  }

  return (
    <div className="auth-form">
      <header className="auth-heading">
        <h1>Welcome back</h1>
        <p>Log in to your Cardfolio account.</p>
      </header>

      <form
        onSubmit={handleSubmit}
        aria-busy={isSubmitting}
        aria-describedby={error ? errorId : undefined}
      >
        {/* Reserve error rendering for feedback supplied by the request handler. */}
        {error && <p id={errorId} className="auth-error" role="alert">{error}</p>}

        <fieldset className="auth-fields" disabled={isSubmitting}>
          <legend className="sr-only">Login details</legend>
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
              autoComplete="current-password"
              placeholder="Enter your password"
              maxLength={128}
              required
            />
          </div>
        </fieldset>

        {/* Native required/email checks run before submission. The button becomes
            available when its handler is supplied; it never simulates a login. */}
        <button
          className="button button-primary auth-submit"
          type="submit"
          disabled={!onSubmit || isSubmitting}
          aria-describedby={!onSubmit ? previewId : undefined}
        >
          {isSubmitting ? 'Logging in…' : 'Log in'}
        </button>

        {!onSubmit && (
          <p id={previewId} className="auth-preview-note">
            Login is unavailable in this UI preview.
          </p>
        )}
      </form>

      <p className="auth-account-prompt">
        New to Cardfolio?{' '}
        <button
          className="auth-text-action"
          type="button"
          onClick={onCreateAccount}
          disabled={!onCreateAccount || isSubmitting}
          title={!onCreateAccount ? 'Account navigation is unavailable' : undefined}
        >
          Create an account
        </button>
      </p>
    </div>
  )
}
