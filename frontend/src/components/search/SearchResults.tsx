import { useId, useState } from 'react'
import charizard from '../../assets/sample-cards/charizard.webp'
import pikachu from '../../assets/sample-cards/pikachu.webp'
import gengar from '../../assets/sample-cards/gengar.webp'
import { Icon } from '../Icon'

// Match the backend's CatalogCardSummary. Search has no set names or prices;
// those arrive when the selected card is imported in the next part of the flow.
export type CatalogCardSummary = {
  provider: string
  provider_card_id: string
  name: string
  card_number: string
  image_url: string | null
}

export type SearchResultsProps = {
  items?: CatalogCardSummary[]
  // Keep this separate from whatever the user is currently typing in the form.
  submittedQuery?: string
  isSearching?: boolean
  error?: string | null
  page?: number
  // The provider doesn't supply a total, so the parent decides when to allow Next.
  canGoNext?: boolean
  onPageChange?: (page: number) => void
  onSelectCard?: (card: CatalogCardSummary) => void
}

function CatalogArtwork({ card }: { card: CatalogCardSummary }) {
  const [imageFailed, setImageFailed] = useState(false)

  // Missing and broken provider images use the same reserved portrait space.
  return (
    <div className="catalog-artwork">
      {card.image_url && !imageFailed ? (
        <img src={card.image_url} alt={`${card.name} Pokémon card`}
          width="600" height="825" loading="lazy" onError={() => setImageFailed(true)} />
      ) : (
        <div className="catalog-artwork-missing">
          <Icon name="cards" />
          <span>Image unavailable</span>
        </div>
      )}
    </div>
  )
}

export function SearchResults({
  items = [], submittedQuery = '', isSearching = false, error = null,
  page = 1, canGoNext = false, onPageChange, onSelectCard,
}: SearchResultsProps) {
  const headingId = useId()
  const query = submittedQuery.trim()

  // Use page numbers without inventing a last page or a total result count.
  // Previous also remains available if a later page returns no matches.
  const pagination = (
    <nav className="catalog-pagination" aria-label="Search results pages">
      <p>Page {page}</p>
      <div>
        <button className="button catalog-page-button" type="button"
          disabled={!onPageChange || page <= 1 || isSearching}
          onClick={() => onPageChange?.(page - 1)}>Previous</button>
        <button className="button catalog-page-button" type="button"
          disabled={!onPageChange || !canGoNext || isSearching}
          onClick={() => onPageChange?.(page + 1)}>Next</button>
      </div>
    </nav>
  )

  if (isSearching) {
    return (
      <section className="catalog-results" aria-labelledby={headingId} aria-busy="true">
        <p className="catalog-section-heading" id={headingId} role="status">Searching the catalog…</p>
        {/* Static placeholders reserve artwork space without adding decorative motion. */}
        <div className="catalog-results-grid catalog-loading-grid" aria-hidden="true">
          {Array.from({ length: 4 }, (_, index) => <div className="catalog-loading-card" key={index} />)}
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="catalog-results catalog-feedback catalog-feedback-error" role="alert" aria-labelledby={headingId}>
        <h2 id={headingId}>Could not search the catalog</h2>
        <p>{error}</p>
        <p>Try searching again in a moment.</p>
      </section>
    )
  }

  if (!query) {
    return (
      <section className="catalog-results catalog-start" aria-labelledby={headingId}>
        {/* Existing artwork gives the initial state context; these are not search results. */}
        <div className="catalog-start-art" aria-hidden="true">
          <img src={charizard} alt="" width="600" height="825" />
          <img src={pikachu} alt="" width="600" height="825" />
          <img src={gengar} alt="" width="600" height="825" />
        </div>
        <div className="catalog-start-copy">
          <h2 id={headingId}>Start with a card name</h2>
          <p>Find the card you have in mind, then choose the right print for your collection.</p>
          <p>Check the artwork and card number to tell similar cards apart.</p>
        </div>
      </section>
    )
  }

  if (!items.length) {
    return (
      <section className="catalog-results" aria-labelledby={headingId}>
        <div className="catalog-feedback" role="status">
          <h2 id={headingId}>No cards found</h2>
          <p>No matches for “{query}” on this page.</p>
          <p>Try another name or check your spelling.</p>
        </div>
        {page > 1 && pagination}
      </section>
    )
  }

  return (
    <section className="catalog-results" aria-labelledby={headingId}>
      <div className="catalog-results-heading">
        <h2 className="catalog-section-heading" id={headingId}>Search results</h2>
        <p role="status">{items.length} {items.length === 1 ? 'card' : 'cards'} on this page for “{query}”</p>
      </div>
      <ul className="catalog-results-grid">
        {items.map(card => (
          <li key={`${card.provider}:${card.provider_card_id}`}>
            <article className="catalog-card">
              {/* A changed image URL gets a fresh fallback state on the next search. */}
              <CatalogArtwork key={card.image_url ?? 'missing'} card={card} />
              <div className="catalog-card-copy">
                <h3>{card.name}</h3>
                <p>Card #{card.card_number}</p>
              </div>
              <button className="button catalog-choose-button" type="button"
                disabled={!onSelectCard}
                aria-label={`Choose ${card.name}, card ${card.card_number}`}
                onClick={() => onSelectCard?.(card)}>Choose card</button>
            </article>
          </li>
        ))}
      </ul>
      {pagination}
    </section>
  )
}
