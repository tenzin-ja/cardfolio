import charizard from '../assets/sample-cards/charizard.webp'
import pikachu from '../assets/sample-cards/pikachu.webp'
import gengar from '../assets/sample-cards/gengar.webp'
import eevee from '../assets/sample-cards/eevee.webp'
import dragonite from '../assets/sample-cards/dragonite.webp'
import blastoise from '../assets/sample-cards/blastoise.webp'
import { Icon } from './Icon'
import { PageHeader } from './PageHeader'

// Static layout samples only. Prices and ownership details are illustrative.
// Image source: https://assets.tcgdex.net/en/base/{set}/{number}/high.webp
// Provider IDs: base1/4, base2/60, base3/5, base2/51, base3/4, base1/2.
// Keep this preview separate so real route components can replace it later.
const sampleCards = [
  { name: 'Charizard', set: 'Base Set', number: '4/102', variant: 'Holofoil', condition: 'Near mint', quantity: 1, price: '$245.00', image: charizard },
  { name: 'Pikachu', set: 'Jungle', number: '60/64', variant: 'Normal', condition: 'Near mint', quantity: 2, price: '$12.50', image: pikachu },
  { name: 'Gengar', set: 'Fossil', number: '5/62', variant: 'Holofoil', condition: 'Lightly played', quantity: 1, price: '$35.00', image: gengar },
  { name: 'Eevee', set: 'Jungle', number: '51/64', variant: 'Normal', condition: 'Near mint', quantity: 1, price: null, image: eevee },
  { name: 'Dragonite', set: 'Fossil', number: '4/62', variant: 'Holofoil', condition: 'Moderately played', quantity: 1, price: '$48.00', image: dragonite },
  { name: 'Blastoise', set: 'Base Set', number: '2/102', variant: 'Holofoil', condition: 'Near mint', quantity: 1, price: '$85.00', image: blastoise },
]

export function CollectionPreview() {
  // Selection is fixed for the preview; real selection state will replace this.
  const featuredCard = sampleCards[0]
  // Count copies, including duplicates, rather than just the number of entries.
  const totalCards = sampleCards.reduce((total, card) => total + card.quantity, 0)

  return (
    <>
      <PageHeader
        title="My collection"
        description={<p>{sampleCards.length} unique cards <span aria-hidden="true">·</span> {totalCards} total cards <span className="sample-label">Sample collection</span></p>}
        actions={
          <>
          {/* These show the intended controls without implying that adding cards
              or switching views is connected yet. */}
          <div className="segmented-control view-picker" role="group" aria-label="Collection view">
            <button className="segment" type="button" aria-pressed="true" disabled aria-describedby="preview-note">
              <Icon name="grid" />Grid
            </button>
            <button className="segment" type="button" aria-pressed="false" disabled aria-describedby="preview-note">
              <Icon name="list" />List
            </button>
          </div>
          <button className="button button-primary" type="button" disabled aria-describedby="preview-note">
            <Icon name="plus" />Add card
          </button>
          </>
        }
      />

      <div className="collection-layout">
        <section aria-label="Sample cards" className="collection-gallery">
          {/* Render every sample with the same layout. The first row loads eagerly;
              later artwork can wait until it approaches the viewport. */}
          <ul className="card-grid">
            {sampleCards.map((card, index) => (
              <li key={card.name}>
                <article className="collection-card" aria-label={`${card.name}, ${card.set}, ${card.number}`}>
                  <div className={`card-artwork${index === 0 ? ' card-artwork-selected' : ''}`}>
                    <img src={card.image} alt={`${card.name} Pokémon card, ${card.set} ${card.number}`}
                      width="600" height="825" loading={index < 3 ? 'eager' : 'lazy'} />
                    {index === 0 && <span className="selected-mark"><Icon name="check" /><span className="sr-only">Shown in card details</span></span>}
                  </div>
                  <div className="card-caption">
                    <h2>{card.name}</h2>
                    <p className="card-set">{card.set} <span aria-hidden="true">·</span> #{card.number}</p>
                    <dl className="card-facts">
                      <div><dt>Variant</dt><dd>{card.variant}</dd></div>
                      <div><dt>Condition</dt><dd>{card.condition}</dd></div>
                      <div><dt>Quantity</dt><dd>{card.quantity}</dd></div>
                      {/* A missing price stays unknown rather than appearing as $0. */}
                      <div className="card-price"><dt>Reference price</dt><dd>{card.price ?? <span aria-label="Price unavailable">—</span>}</dd></div>
                    </dl>
                  </div>
                </article>
              </li>
            ))}
          </ul>
          <p id="preview-note" className="preview-note">Sample cards and prices. Controls are inactive in this design preview.</p>
        </section>

        {/* Reuse the featured card's data so the grid and larger preview agree. */}
        <aside className="card-detail" aria-labelledby="card-detail-heading">
          <div className="detail-label"><span>Card details</span><span className="detail-indicator">Selected</span></div>
          <div className="detail-artwork">
            <img src={featuredCard.image} alt={`${featuredCard.name}, enlarged card artwork`}
              width="600" height="825" />
          </div>
          <div className="detail-copy">
            <h2 id="card-detail-heading">{featuredCard.name}</h2>
            <p className="detail-set">{featuredCard.set} <span aria-hidden="true">·</span> #{featuredCard.number}</p>
            <p className="detail-variant">{featuredCard.variant}</p>
            <dl className="detail-facts">
              <div><dt>Condition</dt><dd>{featuredCard.condition}</dd></div>
              <div><dt>Quantity</dt><dd>{featuredCard.quantity}</dd></div>
              <div><dt>Reference price <span className="currency">USD</span></dt><dd>{featuredCard.price}</dd></div>
            </dl>
            <p className="price-note">Reference prices are estimates, not guaranteed sale values.</p>
          </div>
        </aside>
      </div>
    </>
  )
}
