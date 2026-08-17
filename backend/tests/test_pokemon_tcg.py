from decimal import Decimal

from app.services.pokemon_tcg import map_pokemon_search_response


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