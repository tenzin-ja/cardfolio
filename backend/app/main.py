from fastapi import FastAPI
from app.db.database import Base, engine
from app.models.card import Card

#Look at all models connected to Base and create their tables in the database.
Base. metadata.create_all(bind = engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Cardfolio backend is running"}