import re
from decimal import Decimal
from typing import Any

from app.schemas.catalog import (
    CatalogCardSearchResult,
    CatalogSearchResponse,
    CatalogVariantSearchResult,
)


def normalize_variant_key(provider_key: str) -> str:
    """
    Convert provider camelCase names into Cardfolio snake_case names.

    Example:
        reverseHolofoil -> reverse_holofoil
    """

    return re.sub(
        r"(?<!^)(?=[A-Z])",
        "_",
        provider_key,
    ).lower()


def map_variant_prices(
    card_data: dict[str, Any],
) -> list[CatalogVariantSearchResult]:
    """
    Convert the provider's TCGplayer price dictionary into a stable list.
    """

    # Some cards do not contain TCGplayer data, so each nested lookup needs a
    # safe empty-dictionary fallback.
    tcgplayer_data = card_data.get("tcgplayer") or {}
    provider_prices = tcgplayer_data.get("prices") or {}

    variants = []

    for provider_key, price_data in provider_prices.items():
        # Ignore malformed provider entries rather than crashing while trying
        # to call .get() on a value that is not a dictionary.
        if not isinstance(price_data, dict):
            continue

        market_price = price_data.get("market")

        variants.append(
            CatalogVariantSearchResult(
                variant_key=normalize_variant_key(provider_key),

                # Converting through str avoids carrying a binary float's
                # rounding representation into Decimal.
                market_price=(
                    Decimal(str(market_price))
                    if market_price is not None
                    else None
                ),
                currency="USD",
            )
        )

    # Stable ordering keeps frontend results and tests predictable even if the
    # provider changes the order of its price keys.
    return sorted(
        variants,
        key=lambda variant: variant.variant_key,
    )


def map_pokemon_card(
    card_data: dict[str, Any],
) -> CatalogCardSearchResult:
    """
    Convert one raw Pokemon TCG API card into Cardfolio's search-result schema.
    """

    set_data = card_data["set"]
    image_data = card_data.get("images") or {}

    return CatalogCardSearchResult(
        provider="pokemon_tcg",
        provider_card_id=card_data["id"],
        name=card_data["name"],
        set_id=set_data["id"],
        set_name=set_data["name"],
        card_number=card_data["number"],
        rarity=card_data.get("rarity"),
        image_url=image_data.get("large"),
        variants=map_variant_prices(card_data),
    )


def map_pokemon_search_response(
    response_data: dict[str, Any],
) -> CatalogSearchResponse:
    """
    Convert the complete provider search response into Cardfolio's response.
    """

    return CatalogSearchResponse(
        items=[
            map_pokemon_card(card_data)
            for card_data in response_data["data"]
        ],
        page=response_data["page"],
        page_size=response_data["pageSize"],
        count=response_data["count"],
        total_count=response_data["totalCount"],
    )