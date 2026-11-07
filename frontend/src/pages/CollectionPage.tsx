import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { getCollectionItems, updateCollectionItem } from '../api/collection'
import type { CollectionItem, CollectionItemUpdate } from '../api/collection'
import { CollectionCardDialog } from '../components/CollectionCardDialog'
import { PageHeader } from '../components/PageHeader'
import { CatalogArtwork } from '../components/search/SearchResults'
import { formatCardPrice } from '../components/search/card-price'
import '../components/search/search.css'

type CollectionPageProps = {
  accessToken: string
  onSessionExpired: () => void
}

const PAGE_SIZE = 20

export function CollectionPage({
  accessToken,
  onSessionExpired,
}: CollectionPageProps) {
  const [page, setPage] = useState(1)
  const [hasNextPage, setHasNextPage] = useState(false)
  const [retryAttempt, setRetryAttempt] = useState(0)
  const [items, setItems] = useState<CollectionItem[]>([])
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Read the selected entry from the page we already loaded.
  const selectedItem = items.find(item => item.id === selectedItemId)

  useEffect(() => {
    // Ignore a pending response after leaving the page or changing accounts.
    let ignore = false

    async function loadCollection() {
      setHasNextPage(false)
      setIsLoading(true)
      setError(null)
      setItems([])

      try {
        // Fetch one extra entry to determine whether Next should be available.
        const data = await getCollectionItems(
          accessToken,
          PAGE_SIZE + 1,
          (page - 1) * PAGE_SIZE,
        )

        if (ignore) return

        if (data === null) {
          onSessionExpired()
          return
        }

        // Display only this page. The extra entry belongs to the next page.
        setItems(data.slice(0, PAGE_SIZE))
        setHasNextPage(data.length > PAGE_SIZE)
      } catch (error) {
        if (ignore) return

        setError(
          error instanceof Error
            ? error.message
            : 'Could not load your collection.',
        )
      } finally {
        if (!ignore) setIsLoading(false)
      }
    }

    void loadCollection()

    return () => {
      ignore = true
    }
    // Changing the page or retry counter triggers another request.
  }, [accessToken, onSessionExpired, page, retryAttempt])

  async function handleSaveItem(itemId: number, changes: CollectionItemUpdate) {
    const updatedItem = await updateCollectionItem(accessToken, itemId, changes)
    if (updatedItem === null) {
      onSessionExpired()
      return
    }

    // The dialog and grid read from the same list, so both update in place.
    setItems(current => current.map(item => item.id === itemId ? updatedItem : item))
  }

  return (
    <>
      <PageHeader
        title="My collection"
        description={
          !isLoading && !error ? (
            <p>{items.length} entries on this page</p>
          ) : undefined
        }
        actions={
          <Link className="button button-primary" to="/search">
            Add card
          </Link>
        }
      />

      {isLoading && <p role="status">Loading your collection…</p>}

      {!isLoading && error && (
        <div role="alert">
          <p>{error}</p>
          <button
            className="button"
            type="button"
            onClick={() => setRetryAttempt(attempt => attempt + 1)}
          >
            Retry
          </button>
        </div>
      )}

      {!isLoading && !error && items.length === 0 && (
        <p>
          {page === 1
            ? 'Your collection is empty. Find a card to add your first entry.'
            : 'No entries on this page. Use Previous to go back.'}
        </p>
      )}

      {!isLoading && !error && items.length > 0 && (
        <section className="catalog-results" aria-label="Your collection">
          <ul className="catalog-results-grid">
            {items.map(item => {
              // Card details are nested inside the entry's selected variant.
              const variant = item.card_variant
              const card = variant.catalog_card
              const version = variant.variant_name || variant.variant_key
              const condition = item.condition.replaceAll('_', ' ')

              return (
                // Names can repeat; each owned entry has its own unique ID.
                <li key={item.id}>
                  <article className="collection-card catalog-card">
                    <CatalogArtwork
                      key={card.image_url ?? 'missing'}
                      card={card}
                    />

                    <div className="catalog-card-copy">
                      <h2>{card.name}</h2>
                      <p className="card-set">
                        {card.set_name} · #{card.card_number}
                      </p>

                      <dl className="card-facts">
                        <div>
                          <dt>Variant</dt>
                          <dd>{version}</dd>
                        </div>
                        <div>
                          <dt>Condition</dt>
                          <dd>{condition}</dd>
                        </div>
                        <div>
                          <dt>Quantity</dt>
                          <dd>{item.quantity}</dd>
                        </div>
                        <div className="card-price">
                          <dt>Reference price</dt>
                          <dd>
                            {formatCardPrice(
                              variant.market_price,
                              variant.currency,
                            )}
                          </dd>
                        </div>
                      </dl>
                    </div>
                    <button
                      className="catalog-card-open"
                      type="button"
                      aria-label={`View ${card.name}, ${card.set_name}, card ${card.card_number}, ${version}, ${condition}`}
                      aria-haspopup="dialog"
                      onClick={event => {
                        // Keep the tile as the focus return point after closing.
                        event.currentTarget.focus({ preventScroll: true })
                        setSelectedItemId(item.id)
                      }}
                    />
                  </article>
                </li>
              )
            })}
          </ul>
        </section>
      )}

      {/* Show pagination below the cards; keep Previous available on later pages. */}
      {(items.length > 0 || page > 1) && (
        <nav className="catalog-pagination" aria-label="Collection pages">
          <p>Page {page}</p>

          <div>
            <button
              className="button catalog-page-button"
              type="button"
              disabled={isLoading || page <= 1}
              onClick={() => setPage(current => current - 1)}
            >
              Previous
            </button>

            <button
              className="button catalog-page-button"
              type="button"
              disabled={isLoading || Boolean(error) || !hasNextPage}
              onClick={() => setPage(current => current + 1)}
            >
              Next
            </button>
          </div>
        </nav>
      )}
      {selectedItem && (
        <CollectionCardDialog
          item={selectedItem}
          onClose={() => setSelectedItemId(null)}
          onSave={changes => handleSaveItem(selectedItem.id, changes)}
        />
      )}
    </>
  )
}
