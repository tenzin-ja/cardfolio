import { useId } from 'react'
import type { SubmitEvent, SubmitEventHandler } from 'react'
import { Icon } from '../Icon'

type SearchFormProps = {
  // The page reads the form and makes the request; this component handles display.
  onSubmit?: SubmitEventHandler<HTMLFormElement>
  isSearching?: boolean
}

export function SearchForm({ onSubmit, isSearching = false }: SearchFormProps) {
  const formId = useId()
  const queryId = formId + '-query'
  const hintId = formId + '-hint'
  const unavailableId = formId + '-unavailable'

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    // Keep submission on this page. The parent will supply the search behavior.
    event.preventDefault()
    if (!onSubmit || isSearching) return
    onSubmit(event)
  }

  return (
    <form className="catalog-search-form" role="search" aria-label="Card catalog"
      aria-busy={isSearching} onSubmit={handleSubmit}>
      <fieldset className="catalog-search-fields" disabled={isSearching}>
        <legend className="sr-only">Search the card catalog</legend>
        <div className="catalog-search-field">
          <label htmlFor={queryId}>Card name</label>
          <div className="catalog-search-input">
            <Icon name="search" />
            <input
              id={queryId}
              name="query"
              type="search"
              placeholder="Try Pikachu or Charizard"
              autoComplete="off"
              enterKeyHint="search"
              maxLength={100}
              pattern={'.*\\S.*'}
              title="Enter a card name, rather than only spaces."
              aria-describedby={hintId}
              required
            />
          </div>
        </div>
        <button className="button button-primary catalog-search-submit" type="submit"
          disabled={!onSubmit || isSearching}
          aria-describedby={!onSubmit ? unavailableId : undefined}>
          {isSearching ? 'Searching…' : 'Search'}
        </button>
      </fieldset>
      <p className="catalog-search-hint" id={hintId}>Search Pokémon cards by name.</p>
      {/* Remove this fallback automatically when a real handler is supplied. */}
      {!onSubmit && <p className="catalog-search-unavailable" id={unavailableId} role="status">Search is currently unavailable.</p>}
    </form>
  )
}
