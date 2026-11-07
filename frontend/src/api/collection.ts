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