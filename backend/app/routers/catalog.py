from fastapi import APIRouter, Query

from app.schemas.catalog import CatalogSearchResponse

from app.services.pokemon_tcg import search_pokemon_cards

router = APIRouter(
    prefix = "/catalog",
    tags = ["catalog"]
)

@router.get(
    "/search",
    response_model = CatalogSearchResponse
)
def search_catalog(
    query: str = Query(min_length = 1, max_length = 100),
    page: int = Query(default = 1, ge = 1),
    page_size: int = Query(default = 20, ge = 1, le = 100)
)-> CatalogSearchResponse:
    """
    Search the Pokemon TCG catalog without exposing the provider api key
    """

    # the service reads the api key from the backend env, calls the     
    # provider, and converts its response into cardfolio's catalog schema

    return search_pokemon_cards(
        query = query,
        page = page,
        page_size = page_size
    )

