import httpx

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session 

from app.config import ConfigurationError
from app.db.database import get_db
from app.services.catalog_import import import_catalog_card
from app.schemas.catalog import ( 
    CatalogSearchResponse,
    CatalogImportResponse,
    CatalogImportRequest,
)
from app.services.pokemon_tcg import (
    PokemonTCGResponseError,
    search_pokemon_cards,
    get_pokemon_card
)
router = APIRouter(
    prefix = "/catalog",
    tags = ["catalog"]
)

@router.get(
    "/search",
    response_model = CatalogSearchResponse
)
def search_catalog(
    query: str = Query(min_length = 1, max_length = 100, pattern = r".*\S.*"),
    page: int = Query(default = 1, ge = 1),
    page_size: int = Query(default = 20, ge = 1, le = 100)
)-> CatalogSearchResponse:
    """
    Search the Pokemon TCG catalog without exposing the provider api key
    """

    # the service reads the api key from the backend env, calls the     
    # provider, and converts its response into cardfolio's catalog schema

    try:

        return search_pokemon_cards(
            query = query,
            page = page,
            page_size = page_size
        )
    except ConfigurationError as exc:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "The card catalog is not configured",
        ) from exc

    except PokemonTCGResponseError as exc:
        #The provider replied but sent out unusable data
        raise HTTPException(
            status_code = status.HTTP_502_BAD_GATEWAY,
            detail = "The card catalog provider returned an invalid response."
        )from exc


    # a timeout is also a type of HTTPError, so it must be caught first
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code = status.HTTP_504_GATEWAY_TIMEOUT,
            detail = "The card catalog provider took too long to respond.",
        ) from exc

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code = status.HTTP_502_BAD_GATEWAY,
            detail = "The card catalog provider is currently unavailable.",
        ) from exc

@router.post(
    "/import",
    response_model=CatalogImportResponse,
)
def import_catalog(
    request: CatalogImportRequest,
    db: Session = Depends(get_db)
):
    '''Fetch a provider card and save it in the local catalog'''
    provider_card = get_pokemon_card(request.provider_card_id)

    return import_catalog_card(db,provider_card)