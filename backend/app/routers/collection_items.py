from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session



from app.db.database import get_db
from app.models.card_variant import CardVariant
from app.models.collection_item import CollectionItem
from app.schemas.collection_item import(
    CollectionItemCreate,
    CollectionItemResponse,
)

# The prefix is automatically added to every route defined in this file.
router = APIRouter(
    prefix="/collection-items",
    tags=["collection-items"],
)

@router.post(
    "",
    response_model = CollectionItemResponse,
    status_code = status.HTTP_201_CREATED
)
def create_collection_item(
    item:CollectionItemCreate, 
    db: Session = Depends(get_db),
):
    """
    Validate and save one owned collection item
    """

    #a postive ID can pass pydantic vadliation even if that ID does not
    #belong to a real CardVariant. Checking here gives the client a clear 
    # 404 response isntead of exposing a database IntegreityError/
    card_variant = db.get(CardVariant, item.card_variant_id)

    if card_variant is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Card variant not found"
        )

    #model_dump() converts the pydantic schema into a dict
    # ** unpacks that dict into ColectionItem constructor arguements
    db_item = CollectionItem(**item.model_dump())

    db.add(db_item)
    db.commit()

    # Reload database-generated and default values before returning the object
    db.refresh(db_item)

    return db_item

@router.get(
    "",
    response_model = list[CollectionItemResponse],
)
def get_collection_items(
    #Prevent clients from requesting an unlimited number of records at once.
    limit: int = Query(default = 20, ge = 1, le = 100),
    db: Session = Depends(get_db)
):
    """
    Return saved collection items in a stable order.
    """

    #SQLite does not gaurantee row order unless order_by() is included
    #Ordering by ID gives clients predictable results between requests
    return(
        db.query(CollectionItem)
        .order_by(CollectionItem.id)
        .limit(limit)
        .all()
    )
