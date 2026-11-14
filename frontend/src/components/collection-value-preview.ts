import type { CollectionValueOverviewProps } from './CollectionValueOverview'

// Temporary display data for reviewing the UI before connecting the summary API.
// CollectionPage only renders this preview in a development build.
const now = new Date()
const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
const month = [
  1503.30, 1500.20, 1501.90, 1496.60, 1497.15, 1494.80, 1492.40, 1496.20,
  1490.35, 1491.10, 1487.75, 1483.40, 1486.90, 1485.60, 1481.10, 1478.90,
  1480.75, 1476.40, 1474.80, 1472.15, 1476.20, 1473.70, 1471.15, 1466.45,
  1464.80, 1466.50, 1461.70, 1463.90, 1460.30, 1455.60, 1458.20,
]
const values = Array.from({ length: 60 }, (_, index) =>
  Math.round((1664 - 2.55 * index + Math.sin(index / 3) * 7) * 100) / 100,
).concat(month)

export const collectionValuePreview: CollectionValueOverviewProps = {
  currency: 'USD',
  estimatedValue: values[values.length - 1].toFixed(2),
  totalQuantity: 24,
  pricedQuantity: 21,
  unpricedQuantity: 3,
  isPreview: true,
  history: values.map((value, index) => {
    const date = new Date(today - (values.length - 1 - index) * 86_400_000)
    return {
      snapshot_date: date.toISOString().slice(0, 10),
      observed_at: date.toISOString(),
      currency: 'USD',
      estimated_value: value.toFixed(2),
      total_quantity: 24,
      priced_quantity: 21,
      unpriced_quantity: 3,
    }
  }),
}
