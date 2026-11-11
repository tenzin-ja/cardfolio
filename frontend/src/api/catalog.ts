import type { CatalogCardSummary } from "../components/search/SearchResults";

// one page of serach results returned by the backend
export type CatalogSearchResponse = {
    items: CatalogCardSummary[]
    page: number
    page_size: number
    count: number

    // null means the provider doesn't supply a total
    total_count: number | null
}

export type CatalogImportVariant = {
  // This local database ID is what collection items will reference.
  id: number
  variant_key: string
  variant_name: string | null

  // The backend sends Decimal prices as strings; null means unavailable.
  market_price: string | null
  currency: string
}

// Reuse the search fields, then include the extra details returned by import.
export type CatalogImportResponse = CatalogCardSummary & {
  id: number
  set_id: string
  set_name: string
  rarity: string | null
  variants: CatalogImportVariant[]
}

export type CardPriceObservation = {
  observed_at: string
  market_price: string
  currency: string
}

type VariantPriceHistory = {
  card_variant_id: number
  points: CardPriceObservation[]
}

// Search the catalog and return a complete page of results.
// Start at page 1 unless the caller requests another page.
export async function searchCatalog(
  query: string,
  page = 1,
): Promise<CatalogSearchResponse> {
  const trimmedQuery = query.trim()

  if (!trimmedQuery) {
    throw new Error('Enter a card name to search.')
  }

  // URL parameters must be strings. URLSearchParams also handles
  // spaces and special characters in card names.
  const params = new URLSearchParams({
    query: trimmedQuery,
    page: String(page),
    page_size: '20',
  })

  let response: Response

  try {
    response = await fetch(`/api/catalog/search?${params.toString()}`, {
      method: 'GET',
    })
  } catch {
    // A connection failure throws; HTTP error responses are checked below.
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  if (response.status === 504) {
    throw new Error(
      'The card catalog took too long to respond. Please try again.',
    )
  }

  if (!response.ok) {
    throw new Error('Could not search the catalog. Please try again.')
  }

  return response.json()
}

export async function importCatalogCard(
  providerCardId: string,
): Promise<CatalogImportResponse> {
  let response: Response

  try {
    response = await fetch('/api/catalog/import', {
      method: 'POST',

      // Tell FastAPI that the request body contains JSON.
      headers: {
        'Content-Type': 'application/json',
      },

      // The backend expects snake_case, even though our parameter uses camelCase.
      body: JSON.stringify({
        provider_card_id: providerCardId,
      }),
    })
  } catch {
    // fetch throws for connection failures, not ordinary HTTP error responses.
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  if (response.status === 404) {
    throw new Error('This card could not be found in the catalog.')
  }

  if (response.status === 504) {
    throw new Error('The card catalog took too long to respond. Please try again.')
  }

  if (!response.ok) {
    throw new Error('Could not load this card. Please try again.')
  }

  return response.json()
}

export async function getVariantPriceHistory(
  variantId: number,
  signal: AbortSignal,
): Promise<VariantPriceHistory> {
  const response = await fetch(`/api/catalog/variants/${variantId}/price-history`, { signal })
  if (!response.ok) throw new Error('Could not load price history.')

  const history: VariantPriceHistory = await response.json()
  if (history.card_variant_id !== variantId) throw new Error('Price history belongs to a different version.')
  return history
}
