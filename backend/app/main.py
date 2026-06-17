from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.db.database import Base, engine,SessionLocal
from app.models.card import Card
from app.schemas.card import CardCreate, CardResponse

#Look at all models connected to Base and create their tables in the database.
Base. metadata.create_all(bind = engine)

app = FastAPI()

# This function gives each API request its own database session.
# The session opens before the request runs and closes after the request finishes.

def get_db():
    db = SessionLocal()

    try: 
        yield db 
    finally: 
        db.close()

@app.get("/")
def read_root():
    return {"message": "Cardfolio backend is running"}

'''
When someone sends a POST request to /cards,
use CardCreate to check the incoming data,
save it as a Card database model,
then return it using CardResponse.'''
@app.post("/cards", response_model = CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
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