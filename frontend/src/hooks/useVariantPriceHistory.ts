import { useEffect, useMemo, useState } from 'react'
import { getVariantPriceHistory } from '../api/catalog'
import type { CardPriceObservation } from '../api/catalog'

export function useVariantPriceHistory(variantId: number | undefined) {
  const [retryAttempt, setRetryAttempt] = useState(0)
  // Give each selection or retry its own identity, even when switching A → B → A.
  const request = useMemo(() => ({ variantId, retryAttempt }), [variantId, retryAttempt])
  const [result, setResult] = useState<{
    request: typeof request
    points?: CardPriceObservation[]
    error?: string
  } | null>(null)

  useEffect(() => {
    if (request.variantId === undefined) return

    const controller = new AbortController()
    void getVariantPriceHistory(request.variantId, controller.signal)
      .then(history => {
        if (!controller.signal.aborted) setResult({ request, points: history.points })
      })
      .catch(() => {
        if (!controller.signal.aborted) setResult({ request, error: 'Could not load price history.' })
      })

    // Stop the old request when switching versions or closing the dialog.
    return () => controller.abort()
  }, [request])

  const currentResult = result?.request === request ? result : null
  return {
    points: currentResult?.points,
    error: currentResult?.error,
    isLoading: variantId !== undefined && currentResult === null,
    onRetry: () => setRetryAttempt(attempt => attempt + 1),
  }
}
