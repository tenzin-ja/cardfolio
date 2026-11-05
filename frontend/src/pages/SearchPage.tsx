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


// Keep the response associated with the search that produced it.
type PrefetchedPage = {
  query: string
  data: CatalogSearchResponse
}

// Own the search request here and pass its state into the UI components.
export function SearchPage() {
  const [results, setResults] = useState<CatalogSearchResponse | null>(null)
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  
  function handleCloseCard() {
    // Invalidate the pending response before clearing the dialog.
    importRequestVersion.current += 1
    setSelectedCard(null)
    setImportedCard(null)
    setImportError(null)
    setIsImporting(false)
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
        />
      )}
    </div>
  )
}
