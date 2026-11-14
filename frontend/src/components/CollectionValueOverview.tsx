import { useId, useState } from 'react'
import type { CSSProperties, KeyboardEvent, PointerEvent } from 'react'
import type { CollectionValueHistoryPoint } from '../api/collection'
import { formatCardPrice, readCardPrice } from './search/card-price'
import './collection-value.css'

export type CollectionValueOverviewProps = {
  currency: string
  estimatedValue: string | null
  totalQuantity: number
  pricedQuantity: number
  unpricedQuantity: number
  history: readonly CollectionValueHistoryPoint[]
  asOf?: number
  isRefreshing?: boolean
  error?: string | null
  onRetry?: () => void
}

type Observation = {
  date: string
  timestamp: number
  value: number | null
}

type PricedObservation = Observation & { value: number }

const DAY = 86_400_000
const PLOT_WIDTH = 640
const PLOT_HEIGHT = 240
const ranges = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: 'All', days: null },
] as const

function dateLabel(timestamp: number, includeYear = false) {
  // Snapshots belong to a UTC calendar day, regardless of the viewer's timezone.
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', timeZone: 'UTC',
    ...(includeYear ? { year: 'numeric' } as const : {}),
  }).format(timestamp)
}

export function CollectionValueOverview({
  currency, estimatedValue, totalQuantity, pricedQuantity, unpricedQuantity,
  history, asOf, isRefreshing = false, error = null, onRetry,
}: CollectionValueOverviewProps) {
  const id = useId()
  const [range, setRange] = useState<number | null>(30)
  const [activeDate, setActiveDate] = useState<string | null>(null)
  const [keyboardReadout, setKeyboardReadout] = useState('')
  const [mountedAt] = useState(() => Date.now())
  // A response loaded after UTC midnight advances the range window too.
  const referenceTime = new Date(asOf ?? mountedAt)
  const today = Date.UTC(referenceTime.getUTCFullYear(), referenceTime.getUTCMonth(), referenceTime.getUTCDate())

  const observations: Observation[] = history.flatMap(point => {
    const timestamp = Date.parse(`${point.snapshot_date}T00:00:00Z`)
    if (point.currency !== currency || !Number.isFinite(timestamp)
      || new Date(timestamp).toISOString().slice(0, 10) !== point.snapshot_date) return []
    return [{ date: point.snapshot_date, timestamp, value: readCardPrice(point.estimated_value) }]
  }).sort((a, b) => a.timestamp - b.timestamp)
    .filter((point, index, all) => point.timestamp !== all[index + 1]?.timestamp)
  const visible = observations.filter(point =>
    point.timestamp <= today && (range === null || point.timestamp >= today - range * DAY),
  )
  const priced = visible.filter((point): point is PricedObservation => point.value !== null)
  const first = visible[0]
  const last = visible.at(-1)
  const selected = visible.find(point => point.date === activeDate) ?? last

  const prices = priced.map(point => point.value)
  const low = prices.length ? Math.min(...prices) : 0
  const high = prices.length ? Math.max(...prices) : 0
  const padding = Math.max((high - low) * 0.18, high === low ? high * 0.03 : 0, 0.01)
  const paddedMin = Math.max(0, low - padding)
  const paddedMax = high + padding
  const rawStep = Math.max((paddedMax - paddedMin) / 4, 0.01)
  const magnitude = 10 ** Math.floor(Math.log10(rawStep))
  const normalized = rawStep / magnitude
  const step = (normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10) * magnitude
  const domainMin = Math.floor(paddedMin / step) * step
  const domainMax = Math.ceil(paddedMax / step) * step
  const ticks = Array.from({ length: Math.round((domainMax - domainMin) / step) + 1 }, (_, index) => domainMin + index * step)
  const x = (point: Observation) => !first || !last || first.timestamp === last.timestamp
    ? PLOT_WIDTH / 2
    : (point.timestamp - first.timestamp) / (last.timestamp - first.timestamp) * PLOT_WIDTH
  const y = (value: number) => PLOT_HEIGHT - (value - domainMin) / (domainMax - domainMin) * PLOT_HEIGHT
  const markerStyle = (point: PricedObservation): CSSProperties => ({
    left: `${x(point) / PLOT_WIDTH * 100}%`, top: `${y(point.value) / PLOT_HEIGHT * 100}%`,
  })

  // Keep unknown values in the timeline. Each missing value breaks the line
  // instead of implying a zero value or connecting through an unknown period.
  const segments: PricedObservation[][] = []
  let segment: PricedObservation[] = []
  for (const point of visible) {
    if (point.value === null) {
      segment = []
    } else {
      if (!segment.length) segments.push(segment)
      segment.push({ ...point, value: point.value })
    }
  }

  const currentValue = readCardPrice(estimatedValue)
  const valueText = (value: number | null) => value === null ? 'Value unavailable' : formatCardPrice(value, currency)
  const change = visible.length > 1 && first?.value != null && last?.value != null
    ? last.value - first.value : null
  const percent = change !== null && first?.value ? Math.abs(change / first.value) * 100 : null
  const sign = change !== null && change < 0 ? '−' : '+'
  const changeText = change === null ? null
    : `${sign}${formatCardPrice(Math.abs(change), currency)}${percent === null ? '' : ` (${sign}${percent.toFixed(2)}%)`}`
  const periodText = range === null ? 'over recorded history' : `over ${range} days`
  const coverage = totalQuantity > 0 ? Math.min(100, Math.max(0, pricedQuantity / totalQuantity * 100)) : 0
  let feedback: string | null = null
  let explanation = ''
  if (!observations.length) {
    feedback = 'No history yet'
    explanation = 'Your first recorded value will appear here.'
  } else if (!visible.length) {
    feedback = 'No recorded values in this range'
    explanation = 'Choose All to see your earlier history.'
  } else if (!priced.length) {
    feedback = 'Prices unavailable'
    explanation = 'A value will appear when your cards have reference prices.'
  }

  function selectRange(days: number | null) {
    setRange(days)
    setActiveDate(null)
    setKeyboardReadout('')
  }

  function inspectPoint(event: PointerEvent<SVGSVGElement>) {
    if (!visible.length) return
    const bounds = event.currentTarget.getBoundingClientRect()
    const plotX = (event.clientX - bounds.left) / bounds.width * PLOT_WIDTH
    const nearest = visible.reduce((closest, point) =>
      Math.abs(x(point) - plotX) < Math.abs(x(closest) - plotX) ? point : closest,
    )
    setActiveDate(nearest.date)
  }

  function inspectWithKeyboard(event: KeyboardEvent<SVGSVGElement>) {
    if (!visible.length || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
    event.preventDefault()
    const current = Math.max(0, visible.findIndex(point => point.date === selected?.date))
    const index = event.key === 'Home' ? 0 : event.key === 'End' ? visible.length - 1
      : Math.max(0, Math.min(visible.length - 1, current + (event.key === 'ArrowLeft' ? -1 : 1)))
    const point = visible[index]
    setActiveDate(point.date)
    setKeyboardReadout(`${dateLabel(point.timestamp, true)}: ${valueText(point.value)}`)
  }

  return (
    <section className="collection-value-overview" aria-labelledby={id + '-heading'}>
      <header className="collection-value-heading">
        <div>
          <h2 id={id + '-heading'}>Collection value</h2>
        </div>
        {asOf !== undefined && <p>Loaded <time dateTime={new Date(asOf).toISOString()}>{dateLabel(asOf)}</time> · UTC</p>}
      </header>

      {isRefreshing && <p className="collection-value-refresh-status" role="status">Updating collection value…</p>}
      {error && (
        <div className="collection-value-refresh-error" role="alert">
          <p>{error} Showing the last loaded values.</p>
          {onRetry && <button className="button" type="button" onClick={onRetry}>Try again</button>}
        </div>
      )}

      <div className="collection-value-headline">
        <p className="collection-value-label">Estimated value <span>{currency}</span></p>
        <p className={`collection-value-total${currentValue === null ? ' is-unavailable' : ''}`}>{valueText(currentValue)}</p>
        <p className="collection-value-movement" aria-live="polite">
          {changeText ? <><span className={change === 0 ? '' : change! < 0 ? 'is-negative' : 'is-positive'}>{changeText}</span> {periodText}</>
            : visible.length === 1 && priced.length === 1 ? 'One snapshot. More are needed to show a trend.'
              : 'Not enough history to show a change.'}
        </p>
      </div>

      <div className="collection-value-chart">
        <div className="collection-value-readout" aria-hidden="true">
          {selected && !feedback && <><span>{dateLabel(selected.timestamp, true)}</span><strong>{valueText(selected.value)}</strong></>}
        </div>
        {feedback ? (
          <div className="collection-value-feedback" role="status"><p>{feedback}</p><span>{explanation}</span></div>
        ) : (
          <div className="collection-value-chart-layout">
            <div className="collection-value-plot">
              {ticks.map(tick => <span className="collection-value-y-label" key={tick} style={{ top: `${y(tick) / PLOT_HEIGHT * 100}%` }} aria-hidden="true">{formatCardPrice(tick, currency)}</span>)}
              <svg viewBox={`0 0 ${PLOT_WIDTH} ${PLOT_HEIGHT}`} preserveAspectRatio="none"
                role="img" tabIndex={0} aria-labelledby={`${id}-title ${id}-description`}
                onPointerMove={inspectPoint}
                onPointerLeave={event => { if (event.currentTarget !== document.activeElement) setActiveDate(null) }}
                onKeyDown={inspectWithKeyboard} onBlur={() => setActiveDate(null)}>
                <title id={id + '-title'}>Daily estimated collection value in {currency}</title>
                <desc id={id + '-description'}>
                  {visible.length} recorded daily snapshots. Unknown values leave gaps.
                  Use the left and right arrow keys to inspect values, or Home and End for the first and last.
                </desc>
                <defs><linearGradient id={id + '-fill'} x1="0" y1="0" x2="0" y2="1" className="collection-value-gradient">
                  <stop offset="0%" stopColor="currentColor" stopOpacity="0.19" />
                  <stop offset="100%" stopColor="currentColor" stopOpacity="0.01" />
                </linearGradient></defs>
                {ticks.map(tick => <line className="collection-value-grid" key={tick} x1={0} x2={PLOT_WIDTH} y1={y(tick)} y2={y(tick)} />)}
                {segments.filter(run => run.length > 1).map(run => {
                  const line = run.map((point, index) => `${index ? 'L' : 'M'}${x(point)},${y(point.value)}`).join(' ')
                  return <g key={run[0].date}>
                    <path d={`${line} L${x(run[run.length - 1])},${PLOT_HEIGHT} L${x(run[0])},${PLOT_HEIGHT} Z`} fill={`url(#${id}-fill)`} />
                    <path className="collection-value-line" d={line} fill="none" />
                  </g>
                })}
                {activeDate && selected && <line className="collection-value-crosshair" x1={x(selected)} x2={x(selected)} y1={0} y2={PLOT_HEIGHT} />}
              </svg>
              {/* HTML markers and axis labels keep a fixed, readable size while
                  the SVG stretches to fit the available screen width. */}
              {segments.filter(run => run.length === 1).map(run => <span key={run[0].date} className="collection-value-dot" style={markerStyle(run[0])} aria-hidden="true" />)}
              {last?.value != null && <span className="collection-value-dot" style={markerStyle({ ...last, value: last.value })} aria-hidden="true" />}
              {activeDate && selected?.value != null && <span className="collection-value-dot" style={markerStyle({ ...selected, value: selected.value })} aria-hidden="true" />}
            </div>
            <div className={`collection-value-dates${visible.length === 1 ? ' is-single' : ''}`} aria-hidden="true">
              {first && <span>{dateLabel(first.timestamp)}</span>}
              {first && last && visible.length > 2 && <span className="collection-value-middle-date">{dateLabel((first.timestamp + last.timestamp) / 2)}</span>}
              {last && visible.length > 1 && <span>{dateLabel(last.timestamp)}</span>}
            </div>
          </div>
        )}
        <p className="sr-only" role="status">{keyboardReadout}</p>
      </div>

      <div className="collection-value-range-row">
        <div className="collection-value-ranges" role="group" aria-label="Collection value time range">
          {ranges.map(option => <button key={option.label} type="button" aria-pressed={range === option.days}
            disabled={!observations.length} onClick={() => selectRange(option.days)}>{option.label}</button>)}
        </div>
      </div>

      {/* Keep price coverage together while testing incomplete pricing. */}
      <footer className="collection-value-coverage">
        <div><p><strong>{pricedQuantity} of {totalQuantity}</strong> copies priced</p><p>{unpricedQuantity} without prices</p></div>
        <div className="collection-value-coverage-track" role="img" aria-label={`Reference prices available for ${pricedQuantity} of ${totalQuantity} copies`}>
          <span style={{ width: `${coverage}%` }} />
        </div>
        <p>Includes additions, removals, and reference-price changes.</p>
      </footer>

      {/* The same observations remain available without pointer hover or sight. */}
      <table className="sr-only">
        <caption>Recorded collection values in {currency}</caption>
        <thead><tr><th scope="col">UTC date</th><th scope="col">Estimated value</th></tr></thead>
        <tbody>{visible.map(point => <tr key={point.date}><td>{dateLabel(point.timestamp, true)}</td><td>{valueText(point.value)}</td></tr>)}</tbody>
      </table>
    </section>
  )
}
