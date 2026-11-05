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