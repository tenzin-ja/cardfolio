import type { SubmitEventHandler } from 'react'
import { PageHeader } from '../components/PageHeader'
import { SearchForm } from '../components/search/SearchForm'
import { SearchResults } from '../components/search/SearchResults'
import type { SearchResultsProps } from '../components/search/SearchResults'
import '../components/search/search.css'

export type SearchPageProps = SearchResultsProps & {
  onSubmit?: SubmitEventHandler<HTMLFormElement>
}

// This page composes the UI. Request state and callbacks will be connected here
// during the next guided step; no searches or imports run in these components.
export function SearchPage({ onSubmit, isSearching = false, ...results }: SearchPageProps) {
  return (
    <div className="catalog-search-page">
      <PageHeader title="Find cards" description={<p>Find the right card for your collection.</p>} />
      <SearchForm onSubmit={onSubmit} isSearching={isSearching} />
      <SearchResults {...results} isSearching={isSearching} />
    </div>
  )
}
