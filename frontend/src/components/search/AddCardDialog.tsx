import { useEffect, useId, useRef, useState } from 'react'
import type { SubmitEvent, SubmitEventHandler } from 'react'
import { Icon } from '../Icon'
import { CatalogArtwork } from './SearchResults'
import type { CatalogCardSummary } from './SearchResults'
import { CardPriceChart } from './CardPriceChart'
import type { VariantPriceHistory } from './CardPriceChart'
import { formatCardPrice, readCardPrice } from './card-price'
import type { CardPrice } from './card-price'
import './add-card.css'

// The form only needs this part of the import response. Each variant's local
// database ID is the value the collection request will eventually save.
export type AddCardDetails = {
  set_name: string
  rarity?: string | null
  variants: {
    id: number
    variant_key: string
    variant_name: string | null
    market_price?: CardPrice
    currency?: string
  }[]
}

type AddCardDialogProps = {
  card: CatalogCardSummary
  details?: AddCardDetails | null
  isImporting?: boolean
  importError?: string | null
  isSaving?: boolean
  saveError?: string | null
  priceHistory?: VariantPriceHistory | null
  isHistoryLoading?: boolean
  historyError?: string | null
  onRetryHistory?: () => void
  onVariantChange?: (variantId: number) => void
  onRetryImport?: () => void
  onSubmit?: SubmitEventHandler<HTMLFormElement>
  onClose: () => void
}

export function AddCardDialog({
  card,
  details = null,
  isImporting = false,
  importError = null,
  isSaving = false,
  saveError = null,
  priceHistory = null,
  isHistoryLoading = false,
  historyError = null,
  onRetryHistory,
  onVariantChange,
  onRetryImport,
  onSubmit,
  onClose,
}: AddCardDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null)
  const formId = useId()
  const titleId = formId + '-title'
  const descriptionId = formId + '-description'
  const quantityId = formId + '-quantity'
  const conditionId = formId + '-condition'
  const conditionHintId = formId + '-condition-hint'
  const statusId = formId + '-status'
  const saveErrorId = formId + '-save-error'
  const variants = details?.variants ?? []
  // Start with the first returned version, then keep the visitor's choice.
  // The same selection controls the price, chart, and submitted variant ID.
  const selectedVariant = variants.find(variant => variant.id === selectedVariantId) ?? variants[0]
  const currency = selectedVariant?.currency ?? 'USD'
  const variantName = selectedVariant
    ? selectedVariant.variant_name || selectedVariant.variant_key.replaceAll('_', ' ')
    : 'Version unavailable'
  const historyPoints = selectedVariant?.id === priceHistory?.card_variant_id
    ? priceHistory?.points
    : undefined
  const fieldsDisabled = isImporting || isSaving || Boolean(importError) || !variants.length
  const canSubmit = Boolean(onSubmit) && !fieldsDisabled

  useEffect(() => {
    const dialog = dialogRef.current
    const trigger = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null

    // showModal makes the search behind the dialog inactive.
    dialog?.showModal()
    return () => {
      dialog?.close()
      // React removes the dialog before cleanup, so restore focus ourselves.
      if (trigger?.isConnected) trigger.focus({ preventScroll: true })
    }
  }, [])

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    // Keep submission on this page. The parent will read the fields and save.
    event.preventDefault()
    if (!canSubmit || !onSubmit) return
    onSubmit(event)
  }

  // These messages describe real states without inventing card details or
  // pretending that an unconnected save button has added anything.
  let status: string | null = null
  if (isImporting) {
    status = 'Loading card versions…'
  } else if (!importError && !details) {
    status = 'Card details are unavailable right now. Please try again later.'
  } else if (!importError && !variants.length) {
    status = 'No versions are available for this card. Choose another card.'
  } else if (!importError && !onSubmit) {
    status = 'Adding cards is currently unavailable.'
  }

  return (
    <dialog
      ref={dialogRef}
      className="add-card-dialog card-inspector"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      onCancel={event => {
        // Escape closes the form, except while a save is in progress.
        event.preventDefault()
        if (!isSaving) onClose()
      }}
    >
      <div className="card-inspector-toolbar">
        <div><Icon name="cards" /><span>Card details</span><span className="card-inspector-number">#{card.card_number}</span></div>
        <button className="card-inspector-close" type="button" onClick={onClose}
          disabled={isSaving} aria-label="Close card details">
          <Icon name="close" />
        </button>
      </div>

      <div className="add-card-body">
        <header className="add-card-heading">
          <h2 id={titleId}>{card.name}</h2>
          <p id={descriptionId}>{details?.set_name || 'Pokémon card'}</p>
          <dl className="card-inspector-metadata">
            <div><dt>Card number</dt><dd>{card.card_number}</dd></div>
            {details?.rarity && <div><dt>Rarity</dt><dd>{details.rarity}</dd></div>}
          </dl>
        </header>

        <div className="card-inspector-art-column">
          <div className="add-card-preview">
            <CatalogArtwork card={card} />
          </div>

          <fieldset className="card-version-picker" disabled={fieldsDisabled}>
            <legend>Card version</legend>
            {variants.length ? (
              <div className="card-version-options">
                {variants.map(variant => (
                  <label key={variant.id} className={`card-version-option${selectedVariant?.id === variant.id ? ' is-selected' : ''}`}>
                    {/* form associates this radio with the add form even though
                        the artwork column sits outside that form in the layout. */}
                    <input type="radio" name="card_variant_id" form={formId}
                      value={variant.id} checked={selectedVariant?.id === variant.id}
                      onChange={() => {
                        setSelectedVariantId(variant.id)
                        onVariantChange?.(variant.id)
                      }} required />
                    <span className="card-version-name">{variant.variant_name || variant.variant_key.replaceAll('_', ' ')}</span>
                    <span className="card-version-price">{formatCardPrice(variant.market_price, variant.currency ?? 'USD')}</span>
                    <span className="card-version-marker" aria-hidden="true" />
                  </label>
                ))}
              </div>
            ) : <p className="card-version-empty">{isImporting ? 'Loading card versions…' : 'Versions are not available yet.'}</p>}
          </fieldset>
        </div>

          <section className="card-inspector-pricing" aria-label="Card pricing">
            <div className="card-reference-price">
              <div>
                <p>Reference price <span>· {variantName}</span></p>
                <strong>{formatCardPrice(selectedVariant?.market_price, currency)}</strong>
              </div>
              <span className="card-price-currency">{currency} / card</span>
            </div>
            {selectedVariant && readCardPrice(selectedVariant.market_price) === null && (
              <p className="card-reference-unavailable">No reference price is available for this version.</p>
            )}
            <CardPriceChart points={historyPoints} currency={currency}
              isLoading={isImporting || isHistoryLoading}
              error={historyError} onRetry={onRetryHistory} />
          </section>

        <form
          id={formId}
          className="add-card-form"
          onSubmit={handleSubmit}
          aria-busy={isImporting || isSaving}
        >
          <div className="card-add-heading">
            <h3>Add to collection</h3>
          </div>
          <div className="add-card-feedback">
            {status && <p id={statusId} role="status">{status}</p>}
            {importError && (
              <div className="add-card-error" role="alert">
                <p className="add-card-error-title">Could not load card details</p>
                <p>{importError}</p>
                {onRetryImport && (
                  <button className="add-card-retry" type="button"
                    onClick={onRetryImport} disabled={isImporting || isSaving}>
                    Try again
                  </button>
                )}
              </div>
            )}
          </div>

          <fieldset className="add-card-fields" disabled={fieldsDisabled}>
            <legend className="sr-only">Your card details</legend>

            <div className="add-card-details-row">
              <div className="add-card-field">
                <label htmlFor={quantityId}>Quantity</label>
                <input id={quantityId} name="quantity" type="number"
                  inputMode="numeric" min={1} max={2_147_483_647}
                  step={1} defaultValue={1} required />
              </div>
              <div className="add-card-field">
                <label htmlFor={conditionId}>Condition</label>
                <select id={conditionId} name="condition" defaultValue=""
                  aria-describedby={conditionHintId} required>
                  <option value="" disabled>Select condition</option>
                  <option value="near_mint">Near mint</option>
                  <option value="lightly_played">Lightly played</option>
                  <option value="moderately_played">Moderately played</option>
                  <option value="heavily_played">Heavily played</option>
                  <option value="damaged">Damaged</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
            </div>
            <p className="add-card-condition-hint" id={conditionHintId}>
              Add separate entries for cards in different conditions.
            </p>
          </fieldset>

          {/* A failed save leaves the form mounted, preserving the entered values. */}
          {saveError && (
            <div id={saveErrorId} className="add-card-error" role="alert">
              <p className="add-card-error-title">Could not add this card</p>
              <p>{saveError}</p>
            </div>
          )}

          <div className="add-card-actions">
            <button className="button add-card-cancel" type="button"
              onClick={onClose} disabled={isSaving}>
              Cancel
            </button>
            <button className="button button-primary" type="submit"
              disabled={!canSubmit}
              aria-describedby={importError ? undefined : status ? statusId : saveError ? saveErrorId : undefined}>
              <Icon name="plus" />{isSaving ? 'Adding card…' : 'Add to collection'}
            </button>
          </div>
        </form>
      </div>
    </dialog>
  )
}
