from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.card import Card
from app.schemas.card import CardCreate, CardResponse


# Creates a router that will hold all card-related API routes.
router = APIRouter()


#Creates the API route when someone sends a POST request to /cards
@router.post("/cards", response_model=CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    '''
    When someone sends a POST request to /cards,
    use CardCreate to check the incoming data,
    save it as a Card database model,
    then return it using CardResponse.
    '''   
    # Convert the incoming CardCreate schema into a SQLAlchemy Card model.
    db_card = Card(**card.model_dump())

    #Stage the new card to be saved.
    db.add(db_card)

    # Actually save the card into the databse. 
    db.commit()

    # Refresh the object so it gets the databse-generated id.
    db.refresh(db_card)

    # Return the saved card
    return db_card


@router.get("/cards", response_model=list[CardResponse])
def get_cards(db: Session = Depends(get_db)):
    """
    When someone sends a GET request to /cards,
    query the database for all saved card records,
    then return them as a list using CardResponse.
    """    
    # Query the database for all Card rows.
    cards = db.query(Card).all()

    # Return the list of cards.
    return cards


@router.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: Session = Depends(get_db)):
    """
    When someone sends a GET request to /cards,
    query the database for all saved card records,
    then return them as a list using CardResponse.
    """    
    card = db.query(Card).filter(Card.id == card_id).first()
    # Query the database for all Card rows.

    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    # Return the list of cards.

    return card


@router.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    updated_card: CardCreate,
    db: Session = Depends(get_db)
):
    """
    When someone sends a PATCH request to /cards/{card_id},
    search the database for one card with that id,
    then update only the fields that were provided.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    
    if card is None:
        raise HTTPException(status_code = 404, detial = "Card not Found")
    #Only grab the fields the user actually sent. Doesn't change fields not mentioned 
    update_data = updated_card.model_dump(exclude_unset = True)

    for key, value in update_data.items():
        setattr(card,key,value)
    
    db.commit()
    db.refresh(card)

    return card


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    """
    When someone sends a DELETE request to /cards/{card_id},
    search the database for one card with that id,
    then delete the matching card.
    """
    if card is None:
            raise HTTPException(status_code = 404, detail="Card not found")
    
    db.delete(card)
    db.commit
    return {"message": "Card deleted successfully"}