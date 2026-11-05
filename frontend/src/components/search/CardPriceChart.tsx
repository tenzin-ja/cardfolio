import { useId, useState } from 'react'
import { formatCardPrice, readCardPrice } from './card-price'
import type { CardPrice } from './card-price'

export type CardPriceObservation = {
  observed_at: string
  market_price: CardPrice
  currency: string
}

// Keep the variant ID with its history so changing versions cannot show the
// previous version's prices while the next request is still in progress.
export type VariantPriceHistory = {
  card_variant_id: number
  points: CardPriceObservation[]
}

type CardPriceChartProps = {
  points?: CardPriceObservation[]
  currency: string
  isLoading?: boolean
  error?: string | null
  onRetry?: () => void
}

const ranges = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: 'All', days: null },
] as const

export function CardPriceChart({
  points, currency, isLoading = false, error = null, onRetry,
}: CardPriceChartProps) {
  const [range, setRange] = useState<number | null>(30)
  const chartId = useId()
  const now = Date.now()

  // A chart compares one currency at a time. Missing or invalid observations
  // are skipped, rather than being drawn as a zero-dollar price.
  const observations = (points ?? []).flatMap(point => {
    const price = readCardPrice(point.market_price)
    const timestamp = Date.parse(point.observed_at)
    if (price === null || !Number.isFinite(timestamp) || point.currency !== currency) return []
    return [{ price, timestamp, observedAt: point.observed_at }]
  }).sort((a, b) => a.timestamp - b.timestamp)
    .filter((point, index, all) => point.timestamp !== all[index + 1]?.timestamp)
  const visible = observations.filter(point =>
    range === null || point.timestamp >= now - range * 86_400_000,
  )

  const prices = visible.map(point => point.price)
  const low = prices.length ? Math.min(...prices) : null
  const high = prices.length ? Math.max(...prices) : null
  const first = visible[0]
  const last = visible.at(-1)

  // Padding keeps a flat price visible. It changes the scale, never the data.
  const padding = Math.max(((high ?? 0) - (low ?? 0)) * 0.2, (high ?? 0) * 0.03, 0.01)
  const paddedMin = Math.max(0, (low ?? 0) - padding)
  const paddedMax = (high ?? 0) + padding
  // Round the axis to readable steps, while keeping every actual price inside it.
  const rawStep = Math.max((paddedMax - paddedMin) / 2, 0.01)
  const magnitude = 10 ** Math.floor(Math.log10(rawStep))
  const normalizedStep = rawStep / magnitude
  const step = (normalizedStep <= 1 ? 1 : normalizedStep <= 2 ? 2 : normalizedStep <= 5 ? 5 : 10) * magnitude
  const domainMin = Math.floor(paddedMin / step) * step
  const domainMax = Math.ceil(paddedMax / step) * step
  const x = (timestamp: number) => !first || !last || first.timestamp === last.timestamp
    ? 320
    : ((timestamp - first.timestamp) / (last.timestamp - first.timestamp)) * 640
  const y = (price: number) => 148 - ((price - domainMin) / (domainMax - domainMin)) * 148
  const line = visible.map(point => `${x(point.timestamp)},${y(point.price)}`).join(' ')
  const ticks = Array.from({ length: Math.round((domainMax - domainMin) / step) + 1 }, (_, index) => domainMax - index * step)
  const dateLabel = (timestamp: number) => first && last && first !== last && last.timestamp - first.timestamp < 86_400_000
    ? new Date(timestamp).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    : new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const change = first && last && visible.length > 1 ? last.price - first.price : null
  const changeText = change === null ? null : `${change >= 0 ? '+' : '−'}${formatCardPrice(Math.abs(change), currency)}`
  const tickLabel = (price: number) => price < 1_000 ? formatCardPrice(price, currency)
    : new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(price)

  let feedback: string | null = null
  if (isLoading) feedback = 'Loading price history…'
  else if (error) feedback = error
  else if (!observations.length) feedback = 'No price history yet'
  else if (!visible.length) feedback = 'No recorded prices in this range'

  return (
    <section className="card-price-history" aria-labelledby={chartId + '-heading'}>
      <div className="card-history-heading">
        <h3 id={chartId + '-heading'}>Price history</h3>
        <div className="card-history-ranges" role="group" aria-label="Price history range">
          {ranges.map(option => (
            <button key={option.label} type="button" aria-pressed={range === option.days}
              disabled={isLoading || Boolean(error) || !observations.length}
              onClick={() => setRange(option.days)}>
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card-history-plot" aria-busy={isLoading}>
        {feedback ? (
          <div className="card-history-feedback" role={error ? 'alert' : 'status'}>
            <p>{feedback}</p>
            {!isLoading && !error && !observations.length && (
              <span>Recorded prices will appear here as this card is updated.</span>
            )}
            {error && onRetry && <button type="button" onClick={onRetry}>Try again</button>}
          </div>
        ) : (
          <div className="card-chart-layout">
          <div className="card-chart-frame">
            {/* HTML axis labels keep their readable font size on a phone.
                Only the plotted geometry scales with the SVG. */}
            {ticks.map((tick, index) => <span key={index} className="card-chart-y-label"
              style={{ top: `${y(tick) / 148 * 100}%` }}>{tickLabel(tick)}</span>)}
          <svg viewBox="0 0 640 148" preserveAspectRatio="none" role="img" aria-labelledby={`${chartId}-title ${chartId}-description`}>
            <title id={chartId + '-title'}>Recorded reference prices in {currency}</title>
            <desc id={chartId + '-description'}>
              {visible.length} observations. Lowest {formatCardPrice(low, currency)}, highest {formatCardPrice(high, currency)}.
              {visible.length === 1 ? ' One observation is not enough to show a trend.' : ''}
            </desc>
            {ticks.map((tick, index) => (
              <g key={index}>
                <line className="card-chart-grid" x1="0" x2="640" y1={y(tick)} y2={y(tick)} />
              </g>
            ))}
            {/* Time determines horizontal spacing; equally spaced dots would
                falsely imply that imports happened on a regular schedule. */}
            {visible.length > 1 && <polyline className="card-chart-line" points={line} />}
            {last && (
              <circle className="card-chart-last" cx={x(last.timestamp)} cy={y(last.price)} r="4">
                <title>{dateLabel(last.timestamp)}: {formatCardPrice(last.price, currency)}</title>
              </circle>
            )}
          </svg>
          </div>
          <div className={`card-chart-dates${visible.length === 1 ? ' is-single' : ''}`} aria-hidden="true">
            {first && <span>{dateLabel(first.timestamp)}</span>}
            {first && last && visible.length > 2 && last.timestamp > first.timestamp && (
              <span>
                {dateLabel((first.timestamp + last.timestamp) / 2)}
              </span>
            )}
            {last && visible.length > 1 && <span>{dateLabel(last.timestamp)}</span>}
          </div>
          </div>
        )}
      </div>

      {!feedback && visible.length === 1 && (
        <div className="card-history-caption">
          <p>One recorded price. More observations are needed to show a trend.</p>
        </div>
      )}

      <dl className="card-history-summary">
        <div><dt>Period low</dt><dd>{isLoading || error ? '—' : formatCardPrice(low, currency)}</dd></div>
        <div><dt>Period change</dt><dd className={change === null || change === 0 ? '' : change < 0 ? 'card-price-change is-negative' : 'card-price-change'}>
          {isLoading || error ? '—' : changeText ?? '—'}
        </dd></div>
        <div><dt>Period high</dt><dd>{isLoading || error ? '—' : formatCardPrice(high, currency)}</dd></div>
      </dl>

      {!feedback && (
        <details className="card-history-data">
          <summary>View {visible.length} recorded {visible.length === 1 ? 'price' : 'prices'}</summary>
          {/* A table provides the same observations without relying on sight,
              pointer hover, or the ability to read a plotted line. */}
          <div className="card-history-table-scroll">
            <table>
              <caption className="sr-only">Recorded prices in {currency}</caption>
              <thead><tr><th scope="col">Recorded</th><th scope="col">Reference price</th></tr></thead>
              <tbody>{visible.map((point, index) => (
                <tr key={`${point.observedAt}:${index}`}>
                  <td><time dateTime={point.observedAt}>{new Date(point.timestamp).toLocaleString('en-US')}</time></td>
                  <td>{formatCardPrice(point.price, currency)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  )
}
