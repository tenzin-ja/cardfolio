import { useEffect, useRef, useState } from 'react'
import type { SubmitEvent } from 'react'
import { PageHeader } from '../components/PageHeader'
import { SearchForm } from '../components/search/SearchForm'
import { SearchResults } from '../components/search/SearchResults'
import type { CatalogCardSummary } from '../components/search/SearchResults'
import { AddCardDialog } from '../components/search/AddCardDialog'
import '../components/search/search.css'
import { importCatalogCard, searchCatalog } from '../api/catalog'
import type {
  CatalogImportResponse,
  CatalogSearchResponse,
} from '../api/catalog'
import { createCollectionItem } from '../api/collection'
import type { CardCondition } from '../api/collection'


// Keep the response associated with the search that produced it.
type PrefetchedPage = {
  query: string
  data: CatalogSearchResponse
}

type SearchPageProps = {
  accessToken: string
  onSessionExpired: () => void
}

// Own the search request here and pass its state into the UI components.
export function SearchPage({
  accessToken,
  onSessionExpired,
}: SearchPageProps) {

  const [results, setResults] = useState<CatalogSearchResponse | null>(null)
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // A ref changes immediately, preventing two rapid clicks from sending two saves.
  const saveInFlight = useRef(false)

  // Selection only opens the UI. Importing and saving will be connected next.
  const [selectedCard, setSelectedCard] = useState<CatalogCardSummary | null>(null)

  const [importedCard, setImportedCard] =
  useState<CatalogImportResponse | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [importError, setImportError] = useState<string | null>(null)

  // Keep imports separate from the counter used by search and pagination.
  const importRequestVersion = useRef(0)

  // null means there isn't a usable next page cached.
  const [prefetchedPage, setPrefetchedPage] = useState<PrefetchedPage | null>(null)

    // Enable Next only for a nonempty cached page belonging to this search.
  const canGoNext =
    !isSearching &&
    results !== null &&
    prefetchedPage !== null &&
    prefetchedPage.query === submittedQuery &&
    prefetchedPage.data.page === results.page + 1 &&
    prefetchedPage.data.items.length > 0

  // Identify which search or page request is currently active.
  // Changing a ref doesn't trigger another render.
  const requestVersion = useRef(0)




  // React registers this cleanup when the search page opens and runs it when
  // the page closes, invalidating any search or prefetch requests still in progress.
    useEffect(() => {
      return () => {
        // Ignore pending responses after leaving the search page.
        requestVersion.current += 1
        importRequestVersion.current += 1
      }
    }, [])

  async function prefetchNextPage(
    query: string,
    currentPage: CatalogSearchResponse,
    version: number,
  ) {
    // Only check ahead when the current page is full.
    if (currentPage.count !== currentPage.page_size) return

    try {
      const nextPage = await searchCatalog(query, currentPage.page + 1)

      // Another search or page change may have happened while waiting.
      if (version !== requestVersion.current) return

      // Cache only a page that actually contains cards.
      if (nextPage.items.length > 0) {
        setPrefetchedPage({
          query,
          data: nextPage,
        })
      }
    } catch {
      // Keep the current cards visible and Next disabled if this check fails.
    }
  }
  
  // Keep request handling separate so pagination can reuse it later.
  async function loadResults(query: string, page = 1) {
    const version = ++requestVersion.current

    // Discard the previous page's lookahead before starting another request.
    setPrefetchedPage(null)
    setSubmittedQuery(query)
    setIsSearching(true)
    setError(null)
    setResults(null)

    try {
      const data = await searchCatalog(query, page)

      if (version !== requestVersion.current) return

      setResults(data)

      // Run the next-page check in the background.
      // Its errors are handled inside prefetchNextPage.
      void prefetchNextPage(query, data, version)
    } catch (error) {
      if (version !== requestVersion.current) return

      setError(
        error instanceof Error
          ? error.message
          : 'Could not search the catalog. Please try again.',
      )
    } finally {
      if (version === requestVersion.current) {
        setIsSearching(false)
      }
    }
  }

  //Coordinator for when a card is clicked
  //Calls importcatalogcard to recieve info from backend, and handles errors
  async function handleSelectCard(card: CatalogCardSummary) {
  const version = ++importRequestVersion.current

  // Open the dialog immediately, then load its additional details.
  setSelectedCard(card)
  setImportedCard(null)
  setIsImporting(true)
  setImportError(null)

  try {
    const data = await importCatalogCard(card.provider_card_id)

    // The dialog may have closed or another card may have been selected.
    if (version !== importRequestVersion.current) return

    setImportedCard(data)

  } catch (error) {
    if (version !== importRequestVersion.current) return

    setImportError(
      error instanceof Error
        ? error.message
        : 'Could not load this card. Please try again.',
    )

  } finally {
      // An older request must not clear a newer request's loading state.
      if (version === importRequestVersion.current) {
        setIsImporting(false)
      }
    }
  }


  async function handleAddToCollection(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saveInFlight.current || isImporting || !importedCard) return

    // Read the fields before loading state disables them.
    // FormData also includes the version radio linked through its form attribute.
    const formData = new FormData(event.currentTarget)
    const variantId = Number(formData.get('card_variant_id'))
    const quantity = Number(formData.get('quantity'))

    const conditions: CardCondition[] = [
      'near_mint', 'lightly_played', 'moderately_played',
      'heavily_played', 'damaged', 'unknown',
    ]

    // Finding a permitted value validates it and gives it the CardCondition type.
    const condition = conditions.find(value => value === formData.get('condition'))

    if (!condition || !Number.isInteger(quantity) ||
        quantity < 1 || quantity > 2_147_483_647) {
      setSaveError('Enter a valid quantity and choose a condition.')
      return
    }

    // Only save a version belonging to the card currently open.
    if (!importedCard.variants.some(variant => variant.id === variantId)) {
      setSaveError('Choose an available card version.')
      return
    }

    const version = importRequestVersion.current
    saveInFlight.current = true
    setIsSaving(true)
    setSaveError(null)

    try {
      const savedItem = await createCollectionItem(accessToken, {
        card_variant_id: variantId,
        quantity,
        condition,
      })

      // Ignore the result if this page or card was closed while waiting.
      if (version !== importRequestVersion.current) return

      if (savedItem === null) {
        onSessionExpired()
        return
      }

      // Close only after the backend confirms that the item was created.
      handleCloseCard()
    } catch (error) {
      if (version !== importRequestVersion.current) return

      setSaveError(
        error instanceof Error
          ? error.message
          : 'Could not add this card to your collection.',
      )
    } finally {
      saveInFlight.current = false
      if (version === importRequestVersion.current) {
        setIsSaving(false)
      }
    }
  }
    
  
  function handleCloseCard() {
    // Invalidate the pending response before clearing the dialog.
    importRequestVersion.current += 1
    setSelectedCard(null)
    setImportedCard(null)
    setImportError(null)
    setIsImporting(false)
    setSaveError(null)
    setIsSaving(false)
  }


  function handleSearch(event: SubmitEvent<HTMLFormElement>) {
    // Read the fields before loading state disables the form.
    const formData = new FormData(event.currentTarget)
    const query = String(formData.get('query') ?? '').trim()

    void loadResults(query)
  }

  // Show the requested page, using the prefetched response for Next.
  function handlePageChange(targetpage: number) {
    if (isSearching || !results || targetpage < 1) return

    // Only the next page is prefetched, so other pages load normally
    if (targetpage === results.page - 1) {
      void loadResults(submittedQuery, targetpage)
      return
    }

    // Forward navigation requires a verified, nonempty cached page.
    if (
      targetpage !== results.page + 1 ||
      !canGoNext ||
      !prefetchedPage
    ) {
      return
    }

    // Save the response before clearing the cache.
    const cachedPage = prefetchedPage.data
    const version = ++requestVersion.current

    setPrefetchedPage(null)
    setError(null)
    setResults(cachedPage)

    // This page is now visible. Check beyond it only if it's full.
    void prefetchNextPage(submittedQuery, cachedPage, version)
  }
  

  return (
    <div className="catalog-search-page">
      <PageHeader
        title="Find cards"
        description={<p>Find the right card for your collection.</p>}
      />

      <SearchForm
        onSubmit={handleSearch}
        isSearching={isSearching}
      />

      <SearchResults
        items={results?.items ?? []}
        submittedQuery={submittedQuery}
        isSearching={isSearching}
        error={error}
        page={results?.page ?? 1}
        canGoNext={canGoNext}
        onPageChange={handlePageChange}
        // Start the async handler; it handles its own request errors.
        onSelectCard={card => void handleSelectCard(card)}
      />

      {selectedCard && (
        <AddCardDialog
          key={`${selectedCard.provider}:${selectedCard.provider_card_id}`}
          // Use the full imported card once it arrives.
          card={importedCard ?? selectedCard}
          details={importedCard}
          isImporting={isImporting}
          importError={importError}
          onRetryImport={() => void handleSelectCard(selectedCard)}
          onClose={handleCloseCard}
          isSaving={isSaving}
          saveError={saveError}
          onSubmit={event => void handleAddToCollection(event)}
        />
      )}
    </div>
  )
}
