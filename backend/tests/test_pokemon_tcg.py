#HTTP client library that communicates with the poke tcg api
import httpx


from decimal import Decimal

from app.services.pokemon_tcg import (
    get_pokemon_card,
    map_pokemon_search_response,
    search_pokemon_cards,
)

def test_map_pokemon_search_response_normalizes_provider_data():
    provider_response = {
        "data": [
            {
                "id": "base1-4",
                "name": "Charizard",
                "set": {
                    "id": "base1",
                    "name": "Base",
                },
                "number": "4",
                "rarity": "Rare Holo",
                "images": {
                    "large": "https://images.example/charizard.png",
                },
                "tcgplayer": {
                    "prices": {
                        "reverseHolofoil": {
                            "market": 123.45,
                        },
                        "normal": {
                            "market": 10.00,
                        },
                    },
                },
            }
        ],
        "page": 1,
        "pageSize": 20,
        "count": 1,
        "totalCount": 1,
    }

    result = map_pokemon_search_response(provider_response)

    assert result.page == 1
    assert result.page_size == 20
    assert result.count == 1
    assert result.total_count == 1

    assert len(result.items) == 1

    card = result.items[0]

    assert card.provider == "pokemon_tcg"
    assert card.provider_card_id == "base1-4"
    assert card.name == "Charizard"
    assert card.set_id == "base1"
    assert card.set_name == "Base"
    assert card.card_number == "4"
    assert card.rarity == "Rare Holo"
    assert card.image_url == "https://images.example/charizard.png"

    # mapper sorts variants and converts provider camelCase names into
    # Cardfolio's snake_case format.
    assert [variant.variant_key for variant in card.variants] == [
        "normal",
        "reverse_holofoil",
    ]

    # Decimal verifies that money values weren't left as python floats.
    assert [variant.market_price for variant in card.variants] == [
        Decimal("10.0"),
        Decimal("123.45"),
    ]


def test_search_pokemon_cards_requests_provider_and_maps_response(
    monkeypatch,
):
    """
    Check that catalog search sends the expected Pokémon TCG request
    and converts the provider response into Cardfolio's response format.
    """

    # Use a fake key so the test never depends on a developer's local .env file.
    monkeypatch.setenv(
        "POKEMON_TCG_API_KEY",
        "test-api-key",
    )

    # Keep the response small here. The mapper's other test already covers
    # optional fields such as images, prices, and rarity.
    provider_response = {
        "data": [
            {
                "id": "base1-4",
                "name": "Charizard",
                "set": {
                    "id": "base1",
                    "name": "Base",
                },
                "number": "4",
            }
        ],
        "page": 2,
        "pageSize": 10,
        "count": 1,
        "totalCount": 1,
    }

    # This function stands in for the real Pokémon TCG API.
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.host == "api.pokemontcg.io"
        assert request.url.path == "/v2/cards"

        # Query parameters travel through a URL as text, including page numbers.
        assert request.url.params["q"] == 'name:"Charizard"'
        assert request.url.params["page"] == "2"
        assert request.url.params["pageSize"] == "10"

        # Make sure the service actually sends the key it read from the environment.
        assert request.headers["X-Api-Key"] == "test-api-key"

        # a single float timeout applies the same limit to every HTTP stage
        assert request.extensions["timeout"] == {
            "connect": 10.0,
            "read": 10.0,
            "write": 10.0,
            "pool": 10.0
        }

        return httpx.Response(
            status_code=200,
            json=provider_response,
        )

    # Send requests to our fake handler instead of making a real network call.
    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as client:
        result = search_pokemon_cards(
            query="Charizard",
            page=2,
            page_size=10,
            client=client,
        )

    # Confirm the provider response made it through Cardfolio's mapper.
    assert result.page == 2
    assert result.page_size == 10
    assert result.items[0].name == "Charizard"

def test_get_pokemon_card_requests_exact_card_and_maps_response(
    monkeypatch,
):
    """
    Retrieve one provider card by ID and normalize its response.
    """

    monkeypatch.setenv(
        "POKEMON_TCG_API_KEY",
        "test-api-key",
    )

    # A single-card endpoint returns one dictionary under `data`,
    # rather than the list returned by a search.
    provider_response = {
        "data": {
            "id": "base1-4",
            "name": "Charizard",
            "set": {
                "id": "base1",
                "name": "Base",
            },
            "number": "4",
            "rarity": "Rare Holo",
        }
    }

    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.host == "api.pokemontcg.io"
        assert request.url.path == "/v2/cards/base1-4"
        assert request.headers["X-Api-Key"] == "test-api-key"

        assert request.extensions["timeout"] == {
            "connect": 10.0,
            "read": 10.0,
            "write": 10.0,
            "pool": 10.0,
        }

        return httpx.Response(
            status_code=200,
            json=provider_response,
        )

    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as client:
        result = get_pokemon_card(
            provider_card_id="base1-4",
            client=client,
        )

    assert result.provider == "pokemon_tcg"
    assert result.provider_card_id == "base1-4"
    assert result.name == "Charizard"
    assert result.set_name == "Base"
    assert result.card_number == "4"