from decimal import Decimal

import httpx
import pytest

from app.services.tcgdex import (
    TCGdexResponseError,
    get_tcgdex_card,
    search_tcgdex_cards,
)


def test_search_tcgdex_cards_requests_and_maps_results():
    def handle_request(request):
        assert request.method == "GET"
        assert request.url.host == "api.tcgdex.net"
        assert request.url.path == "/v2/en/cards"
        assert request.url.params["name"] == "like:Charizard"
        assert request.url.params["pagination:page"] == "2"
        assert request.url.params["pagination:itemsPerPage"] == "10"
        assert "X-Api-Key" not in request.headers
        assert request.extensions["timeout"] == {
            "connect": 10.0,
            "read": 10.0,
            "write": 10.0,
            "pool": 10.0,
        }

        return httpx.Response(
            200,
            json=[
                {
                    "id": "base1-4",
                    "localId": "4",
                    "name": "Charizard",
                    "image": "https://assets.tcgdex.net/en/base/base1/4",
                },
                {
                    "id": "2024sv-1",
                    "localId": "1",
                    "name": "Charizard",
                },
            ],
        )

    with httpx.Client(
        transport=httpx.MockTransport(handle_request)
    ) as client:
        result = search_tcgdex_cards(
            "Charizard", page=2, page_size=10, client=client
        )

    assert result.page == 2
    assert result.page_size == 10
    assert result.count == 2
    assert result.total_count is None
    assert result.items[0].provider == "tcgdex"
    assert result.items[0].provider_card_id == "base1-4"
    assert result.items[0].card_number == "4"
    assert result.items[0].image_url == (
        "https://assets.tcgdex.net/en/base/base1/4/high.webp"
    )
    assert result.items[1].image_url is None


def test_get_tcgdex_card_preserves_variants_and_prices():
    # One pricing block can contain multiple finishes.
    # Each variant must pick its own finish, not the first available price.
    pricing = {
        "tcgplayer": {
            "unit": "USD",
            "normal": {"marketPrice": 0.24},
            "reverse-holofoil": {"marketPrice": 0.42},
        }
    }
    provider_response = {
        "id": "swsh3-136",
        "localId": "136",
        "name": "Furret",
        "set": {"id": "swsh3", "name": "Darkness Ablaze"},
        "variants_detailed": [
            {
                "variantId": "normal-version",
                "type": "normal",
                "pricing": pricing,
            },
            {
                "variantId": "reverse-version",
                "type": "reverse",
                "pricing": pricing,
            },
            {
                "variantId": "unpriced-version",
                "type": "normal",
                "pricing": {"tcgplayer": None},
            },
        ],
        # An unpriced variant must not inherit the card-level price.
        "pricing": pricing,
    }

    def handle_request(request):
        assert request.method == "GET"
        assert request.url.host == "api.tcgdex.net"
        assert request.url.path == "/v2/en/cards/swsh3-136"
        return httpx.Response(200, json=provider_response)

    with httpx.Client(
        transport=httpx.MockTransport(handle_request)
    ) as client:
        result = get_tcgdex_card("swsh3-136", client=client)

    assert result.provider == "tcgdex"
    assert result.provider_card_id == "swsh3-136"
    assert result.name == "Furret"
    assert result.set_name == "Darkness Ablaze"
    assert result.card_number == "136"

    assert [variant.variant_key for variant in result.variants] == [
        "normal-version",
        "reverse-version",
        "unpriced-version",
    ]
    assert [variant.market_price for variant in result.variants] == [
        Decimal("0.24"),
        Decimal("0.42"),
        None,
    ]
    assert all(variant.currency == "USD" for variant in result.variants)


@pytest.mark.parametrize(
    "lookup",
    [search_tcgdex_cards, get_tcgdex_card],
)
def test_tcgdex_rejects_invalid_responses(lookup):
    def handle_request(request):
        return httpx.Response(200, json={})

    with httpx.Client(
        transport=httpx.MockTransport(handle_request)
    ) as client:
        with pytest.raises(TCGdexResponseError):
            lookup("base1-4", client=client)