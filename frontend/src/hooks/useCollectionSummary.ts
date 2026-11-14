import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { getCollectionSummary } from '../api/collection'
import type { CollectionSummary } from '../api/collection'

export function useCollectionSummary(accessToken: string, onSessionExpired: () => void) {
  const [refreshAttempt, setRefreshAttempt] = useState(0)
  const request = useMemo(() => ({ accessToken, refreshAttempt }), [accessToken, refreshAttempt])
  const [result, setResult] = useState<{
    request: typeof request
    summary?: CollectionSummary
    loadedAt?: number
    error?: string
  } | null>(null)
  const sessionExpired = useRef(onSessionExpired)

  // A new callback alone should not restart the request. Always call its latest version.
  useEffect(() => {
    sessionExpired.current = onSessionExpired
  }, [onSessionExpired])

  useEffect(() => {
    const controller = new AbortController()

    void getCollectionSummary(request.accessToken, controller.signal)
      .then(summary => {
        if (controller.signal.aborted) return
        if (summary === null) {
          sessionExpired.current()
          return
        }
        setResult({ request, summary, loadedAt: Date.now() })
      })
      .catch(error => {
        if (controller.signal.aborted) return
        setResult(previous => ({
          request,
          // Keep the last successful values during a refresh failure, but never
          // carry one account's data into a different account's session.
          summary: previous?.request.accessToken === request.accessToken ? previous.summary : undefined,
          loadedAt: previous?.request.accessToken === request.accessToken ? previous.loadedAt : undefined,
          error: error instanceof Error ? error.message : 'Could not load your collection value.',
        }))
      })

    // Ignore even an already-resolving response after refresh, logout, or unmount.
    return () => controller.abort()
  }, [request])

  const refresh = useCallback(() => setRefreshAttempt(attempt => attempt + 1), [])
  const sameAccount = result?.request.accessToken === accessToken
  return {
    summary: sameAccount ? result?.summary : undefined,
    loadedAt: sameAccount ? result?.loadedAt : undefined,
    isLoading: result?.request !== request,
    error: result?.request === request ? result.error ?? null : null,
    refresh,
  }
}
