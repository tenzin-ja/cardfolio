from fastapi import FastAPI
from app import models # Registsers all SQLAlchemy models
from app.routers import auth, catalog, collection_items

#Create FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Cardfolio backend is running"}


# makes the routes defined in collection_items.py available to API clients
app.include_router(collection_items.router)

#makes the external card catalog search avaliable to api clients
app.include_router(catalog.router)

#connect auth endpoints to app
app.include_router(auth.router)