from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import Base, engine,SessionLocal
from app.models.card import Card
from app.schemas.card import CardCreate, CardResponse

#Look at all models connected to Base and create their tables in the database.
Base. metadata.create_all(bind = engine)

app = FastAPI()

# This function gives each API request its own database session.
# The session opens before the request runs and closes after the request finishes.
"""
Function creates a new session everytime its called
Session opens before each new api request, then closes afterwards.

"""
def get_db():
    db = SessionLocal()
    
    #after creating new session, stays open until request is finished in route using yield, then closes
    try: 
        yield db 
    finally: 
        db.close()

@app.get("/")
def read_root():
    return {"message": "Cardfolio backend is running"}

#Creates the API route when someone sends a POST request to /cards
@app.post("/cards", response_model = CardResponse)
#
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

@app.get("/cards", response_model=list[CardResponse])
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


@app.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: Session = Depends(get_db)):
    """
    When someone sends a GET request to /cards/{card_id},
    search the database for one card with that id,
    then return the matching card.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    #if card isn't found throw error
    if card is None:
        raise HTTPException(status_code = 404, detail="Card not found")
    return card

"""
When someone sends a DELETE request to /cards/{card_id},
search the database for one card with that id,
then delete the matching card.
"""
@app.delete("/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()

    if card is none:
            raise HTTPException(status_code = 404, detail="Card not found")
    
    db.delete(card)
    db.commit
    return {"message": "Card deleted successfully"}