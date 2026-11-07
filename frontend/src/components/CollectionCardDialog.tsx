import { useEffect, useId, useRef, useState } from 'react'
import type { SubmitEvent } from 'react'
import type { CardCondition, CollectionItem, CollectionItemUpdate } from '../api/collection'
import { Icon } from './Icon'
import { CardPriceChart } from './search/CardPriceChart'
import { CatalogArtwork } from './search/SearchResults'
import { formatCardPrice, readCardPrice } from './search/card-price'
import './search/add-card.css'

type CollectionCardDialogProps = {
  item: CollectionItem
  onClose: () => void
  onSave: (changes: CollectionItemUpdate) => Promise<void>
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

export function CollectionCardDialog({ item, onClose, onSave }: CollectionCardDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const detailsHeadingRef = useRef<HTMLHeadingElement>(null)
  const saveInFlight = useRef(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const titleId = useId()
  const setId = useId()
  const detailsId = useId()
  const priceId = useId()
  const quantityId = useId()
  const conditionId = useId()
  const variant = item.card_variant
  const card = variant.catalog_card
  const version = variant.variant_name || variant.variant_key.replaceAll('_', ' ')
  const hasPrice = readCardPrice(variant.market_price) !== null

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

  function finishEditing() {
    setIsEditing(false)
    setSaveError(null)
    detailsHeadingRef.current?.focus({ preventScroll: true })
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saveInFlight.current) return

    const form = new FormData(event.currentTarget)
    const quantity = Number(form.get('quantity'))
    const condition = conditionOptions.find(option => option.value === form.get('condition'))?.value
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > MAX_QUANTITY || !condition) {
      setSaveError('Enter a valid quantity and choose a condition.')
      return
    }

    // Send only the fields the user changed. Quantity is the new total.
    const changes: CollectionItemUpdate = {}
    if (quantity !== item.quantity) changes.quantity = quantity
    if (condition !== item.condition) changes.condition = condition
    if (Object.keys(changes).length === 0) {
      finishEditing()
      return
    }

    saveInFlight.current = true
    setIsSaving(true)
    setSaveError(null)
    try {
      await onSave(changes)
      finishEditing()
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Could not save changes. Please try again.')
    } finally {
      saveInFlight.current = false
      setIsSaving(false)
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="add-card-dialog collection-card-dialog"
      aria-labelledby={titleId}
      aria-describedby={setId}
      onCancel={event => {
        // Let the parent clear its selection when Escape closes the dialog.
        event.preventDefault()
        if (!saveInFlight.current) onClose()
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
          disabled={isSaving}
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
          <CardPriceChart currency={variant.currency} />
        </section>

        <section className="add-card-form" aria-labelledby={detailsId}>
          <div className="card-add-heading">
            <h3 id={detailsId} ref={detailsHeadingRef} tabIndex={-1}>Collection details</h3>
          </div>
          {isEditing ? (
            <form onSubmit={handleSubmit}>
              <fieldset className="add-card-fields" disabled={isSaving}>
                <legend className="sr-only">Edit collection details</legend>
                <div className="add-card-details-row">
                  <div className="add-card-field">
                    <label htmlFor={quantityId}>Quantity</label>
                    <input id={quantityId} name="quantity" type="number" inputMode="numeric"
                      min={1} max={MAX_QUANTITY} step={1} defaultValue={item.quantity} autoFocus required />
                  </div>
                  <div className="add-card-field">
                    <label htmlFor={conditionId}>Condition</label>
                    <select id={conditionId} name="condition" defaultValue={item.condition} required>
                      {conditionOptions.map(({ value, label }) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </fieldset>
              {saveError && <p className="add-card-error add-card-feedback" role="alert">{saveError}</p>}
              <div className="add-card-actions">
                <button className="button add-card-cancel" type="button"
                  onClick={finishEditing} disabled={isSaving}>Cancel</button>
                <button className="button button-primary" type="submit" disabled={isSaving}>
                  {isSaving ? 'Saving…' : 'Save changes'}
                </button>
              </div>
            </form>
          ) : (
            <>
              <dl className="card-facts">
                <div><dt>Card version</dt><dd>{version}</dd></div>
                <div><dt>Condition</dt><dd>{item.condition.replaceAll('_', ' ')}</dd></div>
                <div><dt>Quantity</dt><dd>{item.quantity}</dd></div>
              </dl>
              <div className="add-card-actions">
                <button className="button add-card-cancel" type="button"
                  onClick={() => setIsEditing(true)}>Edit</button>
              </div>
            </>
          )}
        </section>
      </div>
    </dialog>
  )
}
