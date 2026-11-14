import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { deleteCollectionItem, getCollectionItems, updateCollectionItem } from '../api/collection'
import type { CollectionItem, CollectionItemUpdate } from '../api/collection'
import type { CatalogImportResponse } from '../api/catalog'
import { CollectionCardDialog } from '../components/CollectionCardDialog'
import { CollectionValueOverview } from '../components/CollectionValueOverview'
import { useCollectionSummary } from '../hooks/useCollectionSummary'
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
  const {
    summary,
    loadedAt,
    isLoading: isSummaryLoading,
    error: summaryError,
    refresh: refreshSummary,
  } = useCollectionSummary(accessToken, onSessionExpired)
  const [page, setPage] = useState(1)
  const [hasNextPage, setHasNextPage] = useState(false)
  const [retryAttempt, setRetryAttempt] = useState(0)
  const [items, setItems] = useState<CollectionItem[]>([])
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const addCardLink = useRef<HTMLAnchorElement>(null)
  const focusAfterRemoval = useRef(false)
  const priceRevision = useRef(0)
  // Read the selected entry from the page we already loaded.
  const selectedItem = items.find(item => item.id === selectedItemId)
  // Current TCGdex reference prices are in USD. Never add other currencies to it.
  const currency = 'USD'
  const currencyTotal = summary?.totals_by_currency.find(total => total.currency === currency)
  // An empty collection is worth zero. A nonempty, entirely unpriced one is unknown.
  const estimatedValue = currencyTotal?.estimated_value ?? (summary?.total_quantity === 0 ? '0.00' : null)

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

  useEffect(() => {
    if (selectedItemId !== null || !focusAfterRemoval.current) return
    focusAfterRemoval.current = false
    // The dialog's original focus target was the tile that just disappeared.
    addCardLink.current?.focus()
  }, [selectedItemId])

  async function handleSaveItem(itemId: number, changes: CollectionItemUpdate) {
    const revisionAtSave = priceRevision.current
    const updatedItem = await updateCollectionItem(accessToken, itemId, changes)
    if (updatedItem === null) {
      onSessionExpired()
      return null
    }

    // The dialog and grid read from the same list, so both update in place.
    setItems(current => current.map(item => {
      if (item.id !== itemId) return item
      // A slower save response must not replace prices that refreshed meanwhile.
      return priceRevision.current === revisionAtSave
        ? updatedItem
        : { ...updatedItem, card_variant: item.card_variant }
    }))
    // The save already succeeded. A later summary error belongs to the overview.
    refreshSummary()
    return updatedItem
  }

  const handleCatalogRefreshed = useCallback((card: CatalogImportResponse) => {
    priceRevision.current += 1
    setItems(current => current.map(item => {
      if (item.card_variant.catalog_card.id !== card.id) return item
      const variant = card.variants.find(variant => variant.id === item.card_variant.id)
      if (!variant) return item
      // Conditions and quantities belong to the collection entry, not the catalog.
      return { ...item, card_variant: { ...item.card_variant, ...variant } }
    }))
    refreshSummary()
  }, [refreshSummary])

  async function handleRemoveItem(itemId: number) {
    const removed = await deleteCollectionItem(accessToken, itemId)
    if (removed === null) {
      onSessionExpired()
      return
    }

    focusAfterRemoval.current = true
    setSelectedItemId(null)
    setItems(current => current.filter(item => item.id !== itemId))
    refreshSummary()

    // Reload to fill the empty slot and get the correct Next button state.
    if (page > 1 && items.length === 1 && !hasNextPage) {
      setPage(current => current - 1)
    } else {
      setRetryAttempt(current => current + 1)
    }
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
          <Link ref={addCardLink} className="button button-primary" to="/search">
            Add card
          </Link>
        }
      />

      {summary ? (
        <CollectionValueOverview
          currency={currency}
          estimatedValue={estimatedValue}
          totalQuantity={summary.total_quantity}
          pricedQuantity={summary.priced_quantity}
          unpricedQuantity={summary.unpriced_quantity}
          history={summary.history}
          asOf={loadedAt}
          isRefreshing={isSummaryLoading}
          error={summaryError}
          onRetry={refreshSummary}
        />
      ) : (
        <section className="collection-value-overview collection-value-pending" aria-label="Collection value" aria-busy={isSummaryLoading}>
          <header className="collection-value-heading"><h2>Collection value</h2></header>
          <div className="collection-value-feedback" role={summaryError ? 'alert' : 'status'}>
            <p>{summaryError ?? 'Loading collection value…'}</p>
            {summaryError && <button className="button" type="button" onClick={refreshSummary}>Try again</button>}
          </div>
        </section>
      )}

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
          key={selectedItem.id}
          item={selectedItem}
          onCatalogRefreshed={handleCatalogRefreshed}
          onClose={() => setSelectedItemId(null)}
          onSave={changes => handleSaveItem(selectedItem.id, changes)}
          onRemove={() => handleRemoveItem(selectedItem.id)}
        />
      )}
    </>
  )
}
