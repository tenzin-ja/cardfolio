from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.card_variant import CardVariant
from app.models.catalog_card import CatalogCard
from app.models.price_snapshot import PriceSnapshot
from app.schemas.catalog import CatalogCardSearchResult

PRICE_SOURCE = "tcgplayer"

def import_catalog_card(
        db:Session,
        provider_card: CatalogCardSearchResult,
)-> CatalogCard:
    '''Save a normalized provider card and return its catalog record'''
    catalog_card = (
        db.query(CatalogCard)
        .filter(
            CatalogCard.provider == provider_card.provider,
            CatalogCard.provider_card_id == provider_card.provider_card_id
        )
        .first()
    )
    #if card looking to be imported isn't in database then create an instance of one
    if catalog_card is None:
        catalog_card = CatalogCard(
            provider=provider_card.provider,
            provider_card_id=provider_card.provider_card_id,
            name=provider_card.name,
            set_id=provider_card.set_id,
            set_name=provider_card.set_name,
            card_number=provider_card.card_number,
            rarity=provider_card.rarity,
            image_url=provider_card.image_url,
        )

        db.add(catalog_card)
        db.flush()

    #Create variants the card doesn't already have
    
    #Take the cards existing variants and organize them by their key
    variants_by_key = {
        variant.variant_key: variant
        for variant in catalog_card.variants
    }

    for provider_variant in provider_card.variants:
        variant = variants_by_key.get(provider_variant.variant_key)

        if variant is None:
            variant = CardVariant(
                catalog_card = catalog_card,
                variant_key = provider_variant.variant_key,
                currency = provider_variant.currency
            )

            db.add(variant)
            variants_by_key[provider_variant.variant_key] = variant

            #this block runs as long as there is existing market price data for the variant, 0 inclusive
            if provider_variant.market_price is not None:
                observed_at = datetime.now(timezone.utc)

                variant.market_price = provider_variant.market_price
                variant.market_price_source = PRICE_SOURCE
                variant.market_price_updated_at = observed_at

                snapshot = PriceSnapshot(
                    card_variant=variant,
                    market_price=provider_variant.market_price,
                    currency=provider_variant.currency,
                    source=PRICE_SOURCE,
                    observed_at=observed_at
                )

                db.add(snapshot)
    db.commit()
    db.refresh(catalog_card)

    return catalog_card

