// FastAPI's Decimal prices arrive as strings. These helpers only format the UI;
// the backend remains responsible for storing and calculating monetary values.
export type CardPrice = string | number | null | undefined

export function readCardPrice(value: CardPrice): number | null {
  if (value == null || (typeof value === 'string' && !value.trim())) return null
  const price = Number(value)
  return Number.isFinite(price) && price >= 0 ? price : null
}

export function formatCardPrice(value: CardPrice, currency: string): string {
  const price = readCardPrice(value)
  if (price === null) return 'Price unavailable'
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2,
    }).format(price)
  } catch {
    // An unfamiliar currency code should not break the rest of the card view.
    return `${price.toFixed(2)} ${currency}`
  }
}
