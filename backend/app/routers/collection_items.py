from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session, joinedload


from app.db.database import get_db
from app.models.card_variant import CardVariant
from app.models.collection_item import CollectionItem
from app.schemas.collection_item import(
    CollectionItemCreate,
    CollectionItemResponse,
    CollectionItemUpdate,
)
# Reuse the dependency that validates tokens and retrieves the account.
from app.dependencies import get_current_user
# The database model representing that account.
from app.models.user import User

# The prefix is automatically added to every route defined in this file.
router = APIRouter(
    prefix="/collection-items",
    tags=["collection-items"],
)

@router.post(
    "",
    response_model=CollectionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_collection_item(
    item: CollectionItemCreate,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an entry or increase a matching entry's quantity."""

    card_variant = db.get(CardVariant, item.card_variant_id)

    if card_variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card variant not found",
        )

    # Serialize adds for this account. Without this lock, two requests
    # could both find no matching entry and create separate rows.
    db.query(User).filter(
        User.id == current_user.id,
    ).with_for_update().one()

    # Match every saved field except quantity. This includes the variant,
    # condition, purchase information, and notes, preserving distinct records.
    matching_fields = item.model_dump(exclude={"quantity"})

    existing_item = (
        db.query(CollectionItem)
        .filter_by(
            user_id=current_user.id,
            **matching_fields,
        )
        .order_by(CollectionItem.id)
        .with_for_update()
        .first()
    )

    if existing_item is not None:
        combined_quantity = existing_item.quantity + item.quantity

        # Two individually valid quantities can exceed the database's limit.
        if combined_quantity > 2_147_483_647:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The combined quantity exceeds the supported limit.",
            )

        existing_item.quantity = combined_quantity
        db_item = existing_item

        # Updating an existing entry returns 200; creating one returns 201.
        response.status_code = status.HTTP_200_OK
    else:
        db_item = CollectionItem(
            user_id=current_user.id,
            **item.model_dump(),
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_item)

    return db_item

@router.get(
    "",
    response_model = list[CollectionItemResponse],
)
def get_collection_items(
    limit: int = Query(default=20, ge=1, le=100),
    # This is for pagnation, setting a limit on how many cards will show at a time
    offset: int = Query(default=0,ge=0),
    # Identify the account making this GET request.
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return saved collection items in a stable order.
    """

    # Databases do not guarantee row order without an explicit sort
    # Ordering by ID gives clients predictable results between requests
    return (
        db.query(CollectionItem)
        # Only select rows owned by the signed-in account.
        .filter(CollectionItem.user_id == current_user.id)
        # Include the related variant and card details in the response.
        .options(
            joinedload(CollectionItem.card_variant)
            .joinedload(CardVariant.catalog_card)
        )
        .order_by(CollectionItem.id)
        .offset(offset)
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
    # Validate the token and retrieve the requesting account.
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update only the collection-item fields supplied by the client.
    """

    # Use the same account lock as POST so an add and an edit cannot race.
    db.query(User).filter(User.id == current_user.id).with_for_update().one()

    #Verifies that user owns card before returning
    db_item = (
    db.query(CollectionItem)
    .filter(
        CollectionItem.id == item_id,          # Match the requested item.
        CollectionItem.user_id == current_user.id,  # Match its owner.
    )
    .with_for_update()
    .first()  # Return one matching item, or None.
)

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection item not found",
        )

    # exclude_unset=True distinguishes omitted fields from fields that the
    # client deliberately supplied, including optional fields set to null.
    update_data = item.model_dump(exclude_unset=True)

    # Match the fields used when adding a card. Quantity changes alone
    # can still be saved on older entries that already have duplicates.
    current_match = {
        field: getattr(db_item, field)
        for field in CollectionItemCreate.model_fields
        if field != "quantity"
    }
    updated_match = {
        field: update_data.get(field, value)
        for field, value in current_match.items()
    }
    if updated_match != current_match:
        matching_entry = (
            db.query(CollectionItem.id)
            .filter_by(user_id=current_user.id, **updated_match)
            .filter(CollectionItem.id != item_id)
            .first()
        )
        if matching_entry is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This change would duplicate another collection entry.",
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
    item_id: int,
    # Identify the account requesting the deletion.
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    """
    Delete one owned collection item
    """

    #Same thing, verify user and item match before deleting
    db_item = (
        db.query(CollectionItem)
        .filter(
            CollectionItem.id == item_id,  # Find the requested item.
            CollectionItem.user_id == current_user.id,  # Require ownership.
        )
        .first()
    )
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
