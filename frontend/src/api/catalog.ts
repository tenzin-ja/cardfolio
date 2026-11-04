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