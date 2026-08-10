from fastapi import FastAPI

from app.routers import cards, collection_items

#Create FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Cardfolio backend is running"}


# Connect the card routes to the main FastAPI application.
app.include_router(cards.router)

# makes the routes defined in collection_items.py available to API clients
app.include_router(collection_items.router)
