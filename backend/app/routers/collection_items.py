from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session



from app.db.database import get_db
from app.models.card_variant import CardVariant
from app.models.collection_item import CollectionItem
from app.schemas.collection_item import(
    CollectionItemCreate,
    CollectionItemResponse,
    CollectionItemUpdate,
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
    item: CollectionItemCreate, 
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


@router.patch(
    "/{item_id}",
    response_model=CollectionItemResponse,
)
def update_collection_item(
    item_id: int,
    item: CollectionItemUpdate,
    db: Session = Depends(get_db),
):
    """
    Update only the collection-item fields supplied by the client.
    """

    # Retrieve the existing database row before attempting any changes.
    db_item = db.get(CollectionItem, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection item not found",
        )

    # exclude_unset=True distinguishes omitted fields from fields that the
    # client deliberately supplied, including optional fields set to null.
    update_data = item.model_dump(exclude_unset=True)

    # If the client changes the variant, verify the replacement exists before
    # updating the foreign key.
    if "card_variant_id" in update_data:
        card_variant = db.get(
            CardVariant,
            update_data["card_variant_id"],
        )

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection item not found",
        )

    # setattr() dynamically performs assignments such as:
    # db_item.quantity = 2
    # db_item.condition = "damaged"
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)

    return db_item


@router.delete(
    "/{item_id}",
    status_code = status.HTTP_204_NO_CONTENT
)
def delete_collection_item(
    item_id:int,
    db: Session = Depends(get_db)
):

    """
    Delete one owned collection item
    """

    db_item = db.get(CollectionItem, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection item not found",
        )   
    #This removes only the owned CollectionItem. Its shared CaardVariant and 
    # CatalogCard remain avaliable 
    db.delete(db_item)
    db.commit()

    # A successful 204 response intentionally conatains no JSON body
    return Response(status_code = status.HTTP_204_NO_CONTENT)
