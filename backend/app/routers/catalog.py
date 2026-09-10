import httpx

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session 

from app.db.database import get_db
from app.services.catalog_import import import_catalog_card
from app.schemas.catalog import ( 
    CatalogSearchResponse,
    CatalogImportResponse,
    CatalogImportRequest,
)
from app.services.tcgdex import (
    TCGdexResponseError,
    search_tcgdex_cards,
    get_tcgdex_card,
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
    Search TCGdex and return Cardfolio's catalog summaries
    """

    # The service handles the provider request and response mapping
    # This route validates inputs and turns failures into HTTP responses

    try:

        return search_tcgdex_cards(
            query=query,
            page=page,
            page_size=page_size,
        )


    except TCGdexResponseError as exc:
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
    try: 
        provider_card = get_tcgdex_card(request.provider_card_id)

    except TCGdexResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The card catalog provider returned an invalid response."
        )from exc

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The card catalog provider took too long to respond."
        )from exc

    except httpx.HTTPStatusError as exc:
        #A missing card deserved a 404. Other provider errors do not 
        #mean the users request was wrong
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "The requested card was not found in the provider catalog."
            )from exc
        raise HTTPException(
            status_code = status.HTTP_502_BAD_GATEWAY,
            detail = "The card catalog provider is currently unavailable."
        )from exc

    except httpx.HTTPError as exc:
        # catch connection failures after the http errors
        raise HTTPException(
            status_code = status.HTTP_502_BAD_GATEWAY,
            detail = "The card catalog provider is currently unavailable."
        )from exc
    
    # save only after the provider request and response mapping succeed
    return import_catalog_card(db,provider_card)
