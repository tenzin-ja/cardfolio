from fastapi.testclient import TestClient
from sqlalchemny import create_engine
from sqlalchemy import sessionmaker
from sqlalchemy import StaticPool

from app.db.database import Base, get_db
from app.main import app

#Create a temp in-memory database used only for tests.
test_engine = create_engine(
    "sqlite://",
    connect_args = {"check_same_thread": False},
    poolclass = StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = test_engine
)

#Create the card table insde the test datebase
Base.metadata.create_all(bind = test_engine)

# Replace the real database session with the test database session.
def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

#creates a client that can send tst requests to the FastAPI app
client = TestClient(app)

def test_read_root():

    '''
    check that the backend root route is running correctly.
    '''
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Cardfolio backend is running"
    }

def test_create_card():
    '''
    Check that a card can be created successfully
    '''
    response = client.post(
        "/cards",
        json= { 
            "name": "Pikachu",
            "rarity" : "Rare",
            "condition": "Near Mint",
            "price": 25.50
        } 
    )

    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Pikachu"
    assert data["rarity"] == "Rare"
    assert data["condition"] == "Near Mint"
    assert data["price"] == 25.50
    assert "id" in data