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
    # Find this printing by its provider and ID so reimports reuse the saved card.
    catalog_card = (
        db.query(CatalogCard)
        .filter(
            CatalogCard.provider == provider_card.provider,
            CatalogCard.provider_card_id == provider_card.provider_card_id
        )
        .first()
    )
    # Store the card's details the first time this printing is imported.
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
        # Flush assigns the card ID; the full import is committed below.
        db.flush()


    # Match saved variants by key so reimports reuse their existing IDs.
    variants_by_key = {
        variant.variant_key: variant
        for variant in catalog_card.variants
    }

    # A card can have several variants, each with its own price.
    # Save or refresh each one using its provider key.
    for provider_variant in provider_card.variants:
        variant = variants_by_key.get(provider_variant.variant_key)

        # Create the variant only when it isn't already saved.
        if variant is None:
            variant = CardVariant(
                catalog_card=catalog_card,
                variant_key=provider_variant.variant_key,
                currency=provider_variant.currency,
            )

            db.add(variant)
            variants_by_key[provider_variant.variant_key] = variant

        # Refresh prices for both new and existing variants.
        # Missing prices leave the last known value intact.
        if provider_variant.market_price is not None:
            price_changed = (
                variant.market_price != provider_variant.market_price
                or variant.currency != provider_variant.currency
                or variant.market_price_source != PRICE_SOURCE
            )
            observed_at = datetime.now(timezone.utc)

            variant.market_price = provider_variant.market_price
            variant.currency = provider_variant.currency
            variant.market_price_source = PRICE_SOURCE
            variant.market_price_updated_at = observed_at

            # Add history when the price, currency, or source changes.
            if price_changed:
                snapshot = PriceSnapshot(
                    card_variant=variant,
                    market_price=provider_variant.market_price,
                    currency=provider_variant.currency,
                    source=PRICE_SOURCE,
                    observed_at=observed_at,
                )
                db.add(snapshot)

        # Keep the saved label if the provider doesn't supply one.
        if provider_variant.variant_name:
            variant.variant_name = provider_variant.variant_name
    # Save the card, variants, and price history in one transaction.
    db.commit()
    # Reload the saved card before the router builds its response.
    db.refresh(catalog_card)

    return catalog_card

