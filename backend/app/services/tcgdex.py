import httpx

from app.schemas.catalog import CatalogCardSummary, CatalogSearchResponse


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