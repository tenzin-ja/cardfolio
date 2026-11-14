import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { SubmitEvent } from 'react'
import type { CardCondition, CollectionItem, CollectionItemUpdate } from '../api/collection'
import { importCatalogCard } from '../api/catalog'
import type { CatalogImportResponse } from '../api/catalog'
import { useVariantPriceHistory } from '../hooks/useVariantPriceHistory'
import { Icon } from './Icon'
import { CardPriceChart } from './search/CardPriceChart'
import { CatalogArtwork } from './search/SearchResults'
import { formatCardPrice, readCardPrice } from './search/card-price'
import './search/add-card.css'

type CollectionCardDialogProps = {
  item: CollectionItem
  onClose: () => void
  onSave: (changes: CollectionItemUpdate) => Promise<CollectionItem | null>
  onRemove: () => Promise<void>
  onCatalogRefreshed: (card: CatalogImportResponse) => void
}

const conditionOptions: { value: CardCondition; label: string }[] = [
  { value: 'near_mint', label: 'Near mint' },
  { value: 'lightly_played', label: 'Lightly played' },
  { value: 'moderately_played', label: 'Moderately played' },
  { value: 'heavily_played', label: 'Heavily played' },
  { value: 'damaged', label: 'Damaged' },
  { value: 'unknown', label: 'Unknown' },
]
const MAX_QUANTITY = 2_147_483_647

export function CollectionCardDialog({ item, onClose, onSave, onRemove, onCatalogRefreshed }: CollectionCardDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const removeButtonRef = useRef<HTMLButtonElement>(null)
  const keepEntryRef = useRef<HTMLButtonElement>(null)
  const actionInFlight = useRef(false)
  const [quantityDraft, setQuantityDraft] = useState(String(item.quantity))
  const [conditionDraft, setConditionDraft] = useState(item.condition)
  const [isConfirmingRemoval, setIsConfirmingRemoval] = useState(false)
  const [pendingAction, setPendingAction] = useState<'save' | 'remove' | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const titleId = useId()
  const setId = useId()
  const detailsId = useId()
  const priceId = useId()
  const quantityId = useId()
  const conditionId = useId()
  const removalId = useId()
  const removalPromptId = useId()
  const variant = item.card_variant
  const priceHistory = useVariantPriceHistory(variant.id)
  const card = variant.catalog_card
  const [priceRefreshAttempt, setPriceRefreshAttempt] = useState(0)
  const refreshRequest = useMemo(() => ({
    catalogCardId: card.id,
    provider: card.provider,
    providerCardId: card.provider_card_id,
    variantId: variant.id,
    attempt: priceRefreshAttempt,
  }), [card.id, card.provider, card.provider_card_id, variant.id, priceRefreshAttempt])
  const [refreshResult, setRefreshResult] = useState<{
    request: typeof refreshRequest
    error?: string
  } | null>(null)
  const isRefreshingPrice = refreshResult?.request !== refreshRequest
  const priceRefreshError = refreshResult?.request === refreshRequest ? refreshResult.error : null
  const reloadHistory = priceHistory.onRetry
  const version = variant.variant_name || variant.variant_key.replaceAll('_', ' ')
  const hasPrice = readCardPrice(variant.market_price) !== null
  const draftQuantity = Number(quantityDraft)
  const canStepQuantity = Number.isInteger(draftQuantity) && draftQuantity >= 1 && draftQuantity <= MAX_QUANTITY
  const isBusy = pendingAction !== null
  const editDisabled = isBusy || isConfirmingRemoval

  useEffect(() => {
    const controller = new AbortController()
    void importCatalogCard(refreshRequest.providerCardId, controller.signal)
      .then(refreshed => {
        if (controller.signal.aborted) return
        if (refreshed.id !== refreshRequest.catalogCardId
          || refreshed.provider !== refreshRequest.provider
          || refreshed.provider_card_id !== refreshRequest.providerCardId
          || !refreshed.variants.some(variant => variant.id === refreshRequest.variantId)) {
          throw new Error('The catalog returned a different card or version.')
        }
        onCatalogRefreshed(refreshed)
        // Import commits any new price observation before we request history again.
        reloadHistory()
        setRefreshResult({ request: refreshRequest })
      })
      .catch(error => {
        if (controller.signal.aborted) return
        setRefreshResult({
          request: refreshRequest,
          error: error instanceof Error ? error.message : 'Could not refresh reference prices.',
        })
      })

    // Closing or replacing this dialog discards late results. Cancelling the
    // browser request does not undo an import already committed by the backend.
    return () => controller.abort()
  }, [refreshRequest, onCatalogRefreshed, reloadHistory])

  useEffect(() => {
    const dialog = dialogRef.current
    const trigger = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null

    // A native modal keeps focus out of the grid while the details are open.
    dialog?.showModal()
    return () => {
      dialog?.close()
      if (trigger?.isConnected) trigger.focus({ preventScroll: true })
    }
  }, [])

  useEffect(() => {
    if (isConfirmingRemoval) keepEntryRef.current?.focus()
  }, [isConfirmingRemoval])

  function resetDraft(savedItem: CollectionItem) {
    setQuantityDraft(String(savedItem.quantity))
    setConditionDraft(savedItem.condition)
    setActionError(null)
  }

  function cancelRemoval() {
    setIsConfirmingRemoval(false)
    setActionError(null)
    removeButtonRef.current?.focus()
  }

  async function handleRemove() {
    if (actionInFlight.current) return
    actionInFlight.current = true
    setPendingAction('remove')
    setActionError(null)
    try {
      await onRemove()
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not remove the entry. Please try again.')
    } finally {
      actionInFlight.current = false
      setPendingAction(null)
    }
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (actionInFlight.current || isConfirmingRemoval) return

    const form = new FormData(event.currentTarget)
    const quantity = Number(form.get('quantity'))
    const condition = conditionOptions.find(option => option.value === form.get('condition'))?.value
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > MAX_QUANTITY || !condition) {
      setActionError('Enter a valid quantity and choose a condition.')
      return
    }

    // Send only the fields the user changed. Quantity is the new total.
    const changes: CollectionItemUpdate = {}
    if (quantity !== item.quantity) changes.quantity = quantity
    if (condition !== item.condition) changes.condition = condition
    if (Object.keys(changes).length === 0) {
      resetDraft(item)
      return
    }

    actionInFlight.current = true
    setPendingAction('save')
    setActionError(null)
    try {
      const savedItem = await onSave(changes)
      if (savedItem) resetDraft(savedItem)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not save changes. Please try again.')
    } finally {
      actionInFlight.current = false
      setPendingAction(null)
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="add-card-dialog collection-card-dialog"
      aria-labelledby={titleId}
      aria-describedby={setId}
      onCancel={event => {
        event.preventDefault()
        if (actionInFlight.current) return
        if (isConfirmingRemoval) cancelRemoval()
        else onClose()
      }}
    >
      <div className="card-inspector-toolbar">
        <div>
          <Icon name="cards" />
          <span>Saved card</span>
          <span className="card-inspector-number">#{card.card_number}</span>
        </div>
        <button
          className="card-inspector-close"
          type="button"
          onClick={onClose}
          disabled={isBusy}
          aria-label="Close saved card details"
        >
          <Icon name="close" />
        </button>
      </div>

      <div className="add-card-body">
        <header className="add-card-heading">
          <h2 id={titleId}>{card.name}</h2>
          <p id={setId}>{card.set_name}</p>
          <dl className="card-inspector-metadata">
            <div><dt>Card number</dt><dd>{card.card_number}</dd></div>
            {card.rarity && <div><dt>Rarity</dt><dd>{card.rarity}</dd></div>}
          </dl>
        </header>

        <div className="add-card-preview">
          <CatalogArtwork key={card.image_url ?? 'missing'} card={card} />
        </div>

        <section className="card-inspector-pricing" aria-labelledby={priceId}>
          <div className="card-reference-price">
            <div>
              <p id={priceId}>Reference price <span>· {version}</span></p>
              {hasPrice ? (
                <strong>{formatCardPrice(variant.market_price, variant.currency)}</strong>
              ) : (
                <p className="card-reference-unavailable">
                  No reference price is available for this version.
                </p>
              )}
            </div>
            {hasPrice && <span className="card-price-currency">{variant.currency} / card</span>}
          </div>
          {isRefreshingPrice && <p className="collection-price-status" role="status">Checking latest reference price…</p>}
          {!isRefreshingPrice && !priceRefreshError && <p className="collection-price-checked" role="status">Reference price checked.</p>}
          {priceRefreshError && (
            <div className="collection-price-feedback" role="alert">
              <p>{priceRefreshError} Showing saved values.</p>
              <button className="add-card-retry" type="button" onClick={() => setPriceRefreshAttempt(attempt => attempt + 1)}>Try price refresh again</button>
            </div>
          )}
          <CardPriceChart {...priceHistory} currency={variant.currency} />
        </section>

        <section className="add-card-form" aria-labelledby={detailsId}>
          <div className="card-add-heading">
            <h3 id={detailsId}>Collection details</h3>
          </div>
          <form onSubmit={handleSubmit}>
            <fieldset className="add-card-fields" disabled={isBusy}>
              <legend className="sr-only">Edit collection details</legend>
              <div className="add-card-details-row">
                <div className="add-card-field">
                  <label htmlFor={quantityId}>Quantity</label>
                  <div className="collection-quantity">
                    <button
                      type="button"
                      aria-label="Decrease quantity"
                      disabled={isConfirmingRemoval || !canStepQuantity || draftQuantity === 1}
                      onClick={() => setQuantityDraft(String(draftQuantity - 1))}
                    >
                      <Icon name="minus" />
                    </button>
                    <input
                      id={quantityId}
                      name="quantity"
                      type="number"
                      inputMode="numeric"
                      min={1}
                      max={MAX_QUANTITY}
                      step={1}
                      value={quantityDraft}
                      onChange={event => setQuantityDraft(event.currentTarget.value)}
                      disabled={isConfirmingRemoval}
                      required
                    />
                    <button
                      type="button"
                      aria-label="Increase quantity"
                      disabled={isConfirmingRemoval || !canStepQuantity || draftQuantity === MAX_QUANTITY}
                      onClick={() => setQuantityDraft(String(draftQuantity + 1))}
                    >
                      <Icon name="plus" />
                    </button>
                  </div>
                </div>
                <div className="add-card-field">
                  <label htmlFor={conditionId}>Condition</label>
                  <select id={conditionId} name="condition" value={conditionDraft}
                    onChange={event => setConditionDraft(event.currentTarget.value as CardCondition)}
                    disabled={isConfirmingRemoval} required>
                    {conditionOptions.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <button
                  ref={removeButtonRef}
                  className="button collection-remove-button"
                  type="button"
                  aria-label={isConfirmingRemoval ? 'Hide removal confirmation' : 'Remove entry'}
                  aria-expanded={isConfirmingRemoval}
                  aria-controls={isConfirmingRemoval ? removalId : undefined}
                  title="Remove entry"
                  onClick={() => {
                    if (isConfirmingRemoval) cancelRemoval()
                    else {
                      setActionError(null)
                      setIsConfirmingRemoval(true)
                    }
                  }}
                >
                  <Icon name="trash" />
                </button>
              </div>
            </fieldset>
            {actionError && !isConfirmingRemoval && (
              <p className="add-card-error add-card-feedback" role="alert">{actionError}</p>
            )}
            <div className="add-card-actions">
              <button className="button add-card-cancel" type="button"
                onClick={() => resetDraft(item)} disabled={editDisabled}>Cancel</button>
              <button className="button button-primary" type="submit" disabled={editDisabled}>
                {pendingAction === 'save' ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </form>
          {isConfirmingRemoval && (
            <div id={removalId} className="collection-remove-confirmation" role="group" aria-labelledby={removalPromptId}>
              <p id={removalPromptId}>
                Remove {item.quantity} {item.quantity === 1 ? 'copy' : 'copies'} of {card.name} ({version}, {item.condition.replaceAll('_', ' ')}) from your collection?
              </p>
              {actionError && <p className="add-card-error" role="alert">{actionError}</p>}
              <div className="add-card-actions">
                <button ref={keepEntryRef} className="button add-card-cancel" type="button"
                  onClick={cancelRemoval} disabled={isBusy}>Keep entry</button>
                <button className="button collection-remove-confirm" type="button"
                  onClick={handleRemove} disabled={isBusy}>
                  {pendingAction === 'remove' ? 'Removing…' : 'Remove entry'}
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </dialog>
  )
}
