from fastapi import FastAPI

from app.routers import cards

# Create database tables.
Base.metadata.create_all(bind=engine)


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Cardfolio backend is running"}


# Connect the card routes to the main FastAPI application.
app.include_router(cards.router)