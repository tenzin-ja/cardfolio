import { useEffect, useId, useRef } from 'react'
import type { CollectionItem } from '../api/collection'
import { Icon } from './Icon'
import { CardPriceChart } from './search/CardPriceChart'
import { CatalogArtwork } from './search/SearchResults'
import { formatCardPrice, readCardPrice } from './search/card-price'
import './search/add-card.css'

type CollectionCardDialogProps = {
  item: CollectionItem
  onClose: () => void
}

export function CollectionCardDialog({ item, onClose }: CollectionCardDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const setId = useId()
  const detailsId = useId()
  const priceId = useId()
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

  return (
    <dialog
      ref={dialogRef}
      className="add-card-dialog collection-card-dialog"
      aria-labelledby={titleId}
      aria-describedby={setId}
      onCancel={event => {
        // Let the parent clear its selection when Escape closes the dialog.
        event.preventDefault()
        onClose()
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
            <h3 id={detailsId}>Collection details</h3>
          </div>
          <dl className="card-facts">
            <div><dt>Card version</dt><dd>{version}</dd></div>
            <div><dt>Condition</dt><dd>{item.condition.replaceAll('_', ' ')}</dd></div>
            <div><dt>Quantity</dt><dd>{item.quantity}</dd></div>
          </dl>
        </section>
      </div>
    </dialog>
  )
}
