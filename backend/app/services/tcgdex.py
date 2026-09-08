import httpx
from decimal import Decimal, InvalidOperation

import httpx

from app.schemas.catalog import (
    CatalogCardSearchResult,
    CatalogCardSummary,
    CatalogSearchResponse,
    CatalogVariantSearchResult,
)


TCGDEX_CARDS_URL = "https://api.tcgdex.net/v2/en/cards"
TCGDEX_TIMEOUT_SECONDS = 10.0


class TCGdexResponseError(RuntimeError):
    """TCGdex returned data that Cardfolio could not understand."""


def map_tcgdex_card_summary(card_data: dict) -> CatalogCardSummary:
    if not isinstance(card_data, dict):
        raise TypeError("Expected a card object.")

    image_base = card_data.get("image")

    if image_base is not None and not isinstance(image_base, str):
        raise TypeError("Expected an image URL string.")

    return CatalogCardSummary(
        provider="tcgdex",
        provider_card_id=card_data["id"],
        name=card_data["name"],
        card_number=card_data["localId"],
        # TCGdex gives us the image's base URL, without a size or file extension.
        image_url=f"{image_base}/high.webp" if image_base else None,
    )


def search_tcgdex_cards(
    query: str,
    page: int = 1,
    page_size: int = 20,
    client: httpx.Client | None = None,
) -> CatalogSearchResponse:
    params = {
        "name": f"like:{query.strip()}",
        "pagination:page": page,
        "pagination:itemsPerPage": page_size,
    }

    if client is None:
        # Normal app calls create a client and close it after the request.
        with httpx.Client() as default_client:
            response = default_client.get(
                TCGDEX_CARDS_URL,
                params=params,
                timeout=TCGDEX_TIMEOUT_SECONDS,
            )
    else:
        # A supplied client belongs to the caller, so we leave it open.
        response = client.get(
            TCGDEX_CARDS_URL,
            params=params,
            timeout=TCGDEX_TIMEOUT_SECONDS,
        )

    response.raise_for_status()

    try:
        card_data = response.json()

        # Unlike the old API, TCGdex returns a list directly.
        if not isinstance(card_data, list):
            raise TypeError("Expected a list of cards.")

        items = [
            map_tcgdex_card_summary(card)
            for card in card_data
        ]

        return CatalogSearchResponse(
            items=items,
            page=page,
            page_size=page_size,
            count=len(items),
            # The provider doesn't tell us how many matches exist overall.
            total_count=None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TCGdexResponseError(
            "TCGdex returned an invalid search response."
        ) from exc


def map_tcgdex_card(card_data: dict) -> CatalogCardSearchResult:
    # Reuse the basic fields we already map for search results.
    summary = map_tcgdex_card_summary(card_data)
    variants = []

    price_keys = {
        "normal": "normal",
        "holo": "holofoil",
        "reverse": "reverse-holofoil",
    }

    detailed_variants = card_data.get("variants_detailed") or []

    if not isinstance(detailed_variants, list):
        raise TypeError("Expected a list of detailed variants.")

    for variant_data in detailed_variants:
        if not isinstance(variant_data, dict):
            raise TypeError("Expected a variant object.")

        # The provider's ID keeps different editions of the same finish separate.
        variant_key = variant_data["variantId"]

        if not isinstance(variant_key, str) or not 1 <= len(variant_key) <= 50:
            raise ValueError("Invalid variant ID.")

        pricing = variant_data.get("pricing") or {}
        tcgplayer = pricing.get("tcgplayer") or {}
        price_key = price_keys.get(variant_data["type"])
        market_price = None

        # Only use a matching finish from this variant's own USD pricing.
        # Missing prices stay unknown, we don't borrow another edition's price.
        if price_key is not None and tcgplayer.get("unit") == "USD":
            price_data = tcgplayer.get(price_key) or {}
            raw_price = price_data.get("marketPrice")

            if raw_price is not None:
                market_price = Decimal(str(raw_price))

        variants.append(
            CatalogVariantSearchResult(
                variant_key=variant_key,
                market_price=market_price,
                currency="USD",
            )
        )

    return CatalogCardSearchResult(
        **summary.model_dump(),
        set_id=card_data["set"]["id"],
        set_name=card_data["set"]["name"],
        rarity=card_data.get("rarity"),
        variants=variants,
    )


def get_tcgdex_card(
    provider_card_id: str,
    client: httpx.Client | None = None,
) -> CatalogCardSearchResult:
    url = f"{TCGDEX_CARDS_URL}/{provider_card_id}"

    if client is None:
        with httpx.Client() as default_client:
            response = default_client.get(
                url,
                timeout=TCGDEX_TIMEOUT_SECONDS,
            )
    else:
        response = client.get(
            url,
            timeout=TCGDEX_TIMEOUT_SECONDS,
        )

    # Keep HTTP errors separate so the router can recognize a missing card.
    response.raise_for_status()

    try:
        return map_tcgdex_card(response.json())
    except (
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        InvalidOperation,
    ) as exc:
        raise TCGdexResponseError(
            "TCGdex returned an invalid card response."
        ) from exc