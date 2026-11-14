import type { CatalogImportVariant } from './catalog'

export type CardCondition =
  | 'near_mint'
  | 'lightly_played'
  | 'moderately_played'
  | 'heavily_played'
  | 'damaged'
  | 'unknown'

//stores the information of card that'll be sent to backend to be saved
export type CollectionItemCreate = {
  // Use the local variant ID returned by import.
  card_variant_id: number
  quantity: number
  condition: CardCondition
}

export type CollectionItemUpdate = Partial<Pick<CollectionItemCreate, 'quantity' | 'condition'>>

// These are the response fields needed for the save step.
export type CreatedCollectionItem = CollectionItemCreate & {
  id: number
}

// "&" combines both sets of fields at the same level.
// We can read item.quantity, item.condition, and item.id directly.
export type CollectionItem = CreatedCollectionItem & {
  card_variant: CatalogImportVariant & {
    catalog_card: {
      id: number
      provider: string
      provider_card_id: string
      name: string
      set_name: string
      card_number: string
      rarity: string | null
      image_url: string | null
    }
  }
}

// FastAPI sends Decimal amounts as strings; the UI converts them for display only.
export type CollectionValueHistoryPoint = {
  snapshot_date: string
  observed_at: string
  currency: string
  estimated_value: string | null
  total_quantity: number
  priced_quantity: number
  unpriced_quantity: number
}

export type CollectionSummary = {
  total_quantity: number
  priced_quantity: number
  unpriced_quantity: number
  totals_by_currency: { currency: string; estimated_value: string }[]
  history: CollectionValueHistoryPoint[]
}

export async function getCollectionSummary(
  accessToken: string,
  signal?: AbortSignal,
): Promise<CollectionSummary | null> {
  let response: Response

  try {
    response = await fetch('/api/collection-items/summary', {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal,
    })
  } catch (error) {
    // Let the hook discard a cancelled request without showing a network error.
    if (signal?.aborted) throw error
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  if (response.status === 401) return null
  if (!response.ok) {
    throw new Error('Could not load your collection value. Please try again.')
  }

  return response.json()
}



export async function createCollectionItem(
  accessToken: string,
  item: CollectionItemCreate,
): Promise<CreatedCollectionItem | null> {
  let response: Response

  try {
    response = await fetch('/api/collection-items', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',

        // The backend uses this token to identify the collection's owner.
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(item),
    })
  } catch {
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  // Match getCurrentUser: null tells the caller to end the rejected session.
  if (response.status === 401) {
    return null
  }

  if (response.status === 404) {
    throw new Error(
      'This card version could not be found. Reopen the card and try again.',
    )
  }

  if (response.status === 422) {
    throw new Error('Check the card version, quantity, and condition.')
  }

  if (!response.ok) {
    throw new Error('Could not add this card to your collection.')
  }

  return response.json()
}

export async function getCollectionItems(
  accessToken: string,
  limit = 20,
  offset = 0,
): Promise<CollectionItem[] | null> {
  // Collection pagination uses an offset: 0 starts at the first entry.
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })

  let response: Response

  try {
    response = await fetch(`/api/collection-items?${params.toString()}`, {
      method: 'GET',
      headers: {
        // The backend returns only the collection belonging to this token.
        Authorization: `Bearer ${accessToken}`,
      },
    })
  } catch {
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  if (response.status === 401) {
    return null
  }

  if (!response.ok) {
    throw new Error('Could not load your collection. Please try again.')
  }

  // This endpoint returns an array directly, without an "items" wrapper.
  return response.json()
}

export async function updateCollectionItem(
  accessToken: string,
  itemId: number,
  changes: CollectionItemUpdate,
): Promise<CollectionItem | null> {
  let response: Response
  try {
    response = await fetch(`/api/collection-items/${itemId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(changes),
    })
  } catch {
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  if (response.status === 401) return null
  if (response.status === 404) {
    throw new Error('This entry is no longer in your collection. Refresh the page to see your current entries.')
  }
  if (response.status === 409) {
    throw new Error('A matching entry already exists in that condition. Choose another condition or edit the matching entry.')
  }
  if (response.status === 422) {
    throw new Error('Check the quantity and condition, then try again.')
  }
  if (!response.ok) {
    throw new Error('Could not save changes. Please try again.')
  }

  return response.json()
}

export async function deleteCollectionItem(
  accessToken: string,
  itemId: number,
): Promise<true | null> {
  let response: Response
  try {
    response = await fetch(`/api/collection-items/${itemId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${accessToken}` },
    })
  } catch {
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  if (response.status === 401) return null
  // A retry can find the entry already gone if the first response was lost.
  if (response.status === 204 || response.status === 404) return true
  throw new Error('Could not remove the entry. Please try again.')
}
