import re
import httpx


from decimal import Decimal
from typing import Any

from app.config import get_pokemon_tcg_api_key
from app.schemas.catalog import (
    CatalogCardSearchResult,
    CatalogSearchResponse,
    CatalogVariantSearchResult,
)

POKEMON_TCG_CARDS_URL = "https://api.pokemontcg.io/v2/cards"
POKEMON_TCG_TIMEOUT_SECONDS = 10.0

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

def build_pokemon_name_query(query: str) -> str:
    """
    Turn a card name entered by the user into a safe provider search phrase.
    """

    cleaned_query = query.strip()

    # Escape backslashes first so we do not accidentally escape the
    # backslashes added when protecting quotation marks.
    escaped_query = cleaned_query.replace("\\", "\\\\")
    escaped_query = escaped_query.replace('"', '\\"')

    return f'name:"{escaped_query}"'

def search_pokemon_cards(
    query:str,
    page: int = 1,
    page_size: int = 20,
    client: httpx.Client | None = None
) -> CatalogSearchResponse:

    """
    Search the Pokémon TCG catalog by card name.

    Sends an authenticated, paginated request and converts the provider's
    response into Cardfolio's catalog format. Also can choose to do a mocked
    HTTP client if you don't want to make a real network request
    """
    #Convert the users test into the query format to avoid issues with card name inputs
    provider_name_query = build_pokemon_name_query(query)
    
    headers = {
        "X-Api-Key": get_pokemon_tcg_api_key(),
    }
    params = {
    # Turn the name into provider syntax without letting quotes change the search.
        "q":provider_name_query,
        "page": page,
        "pageSize": page_size
    }

    if client is None:
        #normal application calls create their own client and close it here
        with httpx.Client() as default_client:
            response = default_client.get(
                POKEMON_TCG_CARDS_URL,
                headers=headers,
                params=params,
                timeout = POKEMON_TCG_TIMEOUT_SECONDS  
            )
    else:
        #Tests can send in a mocked client so no real network request is made.
        #The caller owns this client so this func shouldn't close it 
        response = client.get(
            POKEMON_TCG_CARDS_URL,
            headers=headers,
            params=params,
            timeout = POKEMON_TCG_TIMEOUT_SECONDS  

        )

    #stops for unsuccessful responses instead of sending error json through regular card data mapper
    response.raise_for_status()
    return map_pokemon_search_response(response.json())

def get_pokemon_card(
    provider_card_id: str,
    client: httpx.Client | None = None,
) -> CatalogCardSearchResult:
    '''
    Get one card using its provider id
    '''

    headers = {
        "X-Api-Key": get_pokemon_tcg_api_key(),
    }
    card_url = (
        f"{POKEMON_TCG_CARDS_URL}/{provider_card_id}"
    )

    if client is None:
        #Normal application calls create and close their own http client
        with httpx.Client() as default_client:
            response = default_client.get(
                card_url,
                headers = headers,
                timeout = POKEMON_TCG_TIMEOUT_SECONDS
            )
    else:
        #tests and reusable callers can provide a client that they own
        response = client.get(
            card_url,                 
            headers=headers,
            timeout = POKEMON_TCG_TIMEOUT_SECONDS,
        )

    response.raise_for_status()

    # a single card reponse contains one dict under 'data'
    # unlike search responses, where 'data' contains a list
    card_data = response.json()["data"]

    return map_pokemon_card(card_data)