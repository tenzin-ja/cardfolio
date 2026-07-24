import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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

@pytest.fixture(autouse=True)
def reset_test_database():
    """
    Start every test with a fresh, empty database.
    """

    #deletes the old test tables and creates fresh empty ones.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield
    #deletes everything again
    Base.metadata.drop_all(bind=test_engine)

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

    #recieves simulated get request from the get route. response saves all info from request
    response = client.get("/")

    #checks the http status code, 200 meaning the request suceeded.
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

def test_get_cards():
    """Check that saved cards can be retrieved."""

    # Create the card needed for this specific test.
    create_response = client.post(
        "/cards",
        json={
            "name": "Pikachu",
            "rarity": "Rare",
            "condition": "Near Mint",
            "price": 25.50
        }
    )

    assert create_response.status_code == 200

    response = client.get("/cards")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Pikachu"

def test_get_cards_filters_by_partial_case_insensitive_name():
    """Return only cards matching a partial name, regardless of case."""

    pikachu_response = client.post(
        "/cards",
        json={"name": "Pikachu"}
    )
    charmander_response = client.post(
        "/cards",
        json={"name": "Charmander"}
    )

    assert pikachu_response.status_code == 200
    assert charmander_response.status_code == 200

    response = client.get(
        "/cards",
        params={"name": "PIKA"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Pikachu"

@pytest.mark.parametrize("invalid_limit", [0, 101])
def test_get_cards_rejects_limit_outside_allowed_range(invalid_limit):
    """
    The API only permits limits from 1 through 100.

    Parametrization runs this test once for each invalid value.
    """
    response = client.get(
        "/cards",
        params={"limit": invalid_limit}
    )

    assert response.status_code == 422

def test_get_cards_respects_valid_limit():
    """Return no more cards than the requested limit"""

    for card_name in ["Pikachu", "Charmander"]:
        create_response = client.post(
            "/cards",
            json={"name": card_name}
        )
        assert create_response.status_code == 200

    response = client.get(
        "/cards",
        params = {"limit" : 1}
    )

    assert response.status_code == 200
    data = response.json()

    #We only check the count because teh endpoint does not define a sorting order yet
    assert len(data) == 1


        

def test_create_card_with_negative_price():
    """
    Check that a card cannot be created with a negative price.
    """
    response = client.post(
        "/cards",
        json={
            "name": "Invalid Card",
            "rarity": "Common",
            "condition": "Near Mint",
            "price": -10
        }
    )

    assert response.status_code == 422

def test_update_card():
    """Check that an existing card can be updated."""

    # Create a card specifically for this test.
    create_response = client.post(
        "/cards",
        json={
            "name": "Bulbasaur",
            "rarity": "Common",
            "condition": "Good",
            "price": 10.00
        }
    )

    card_id = create_response.json()["id"]

    # Update only the price.
    response = client.patch(
        f"/cards/{card_id}",
        json={
            "price": 15.00
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == card_id
    assert data["name"] == "Bulbasaur"
    assert data["price"] == 15.00

def test_delete_card():
    """Check that an existing card can be deleted."""
    
    # Create a card specifically for this test.
    create_response = client.post(
        "/cards",
        json={
            "name": "Squirtle",
            "rarity": "Common",
            "condition": "Good",
            "price": 12.00
        }
    )

    assert create_response.status_code == 200

    card_id = create_response.json()["id"]

    # Delete the card.
    delete_response = client.delete(f"/cards/{card_id}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Card deleted successfully"
    }

    # Deleting it again should return 404 because it no longer exists.
    second_delete_response = client.delete(f"/cards/{card_id}")

    assert second_delete_response.status_code == 404
    assert second_delete_response.json() == {
        "detail": "Card not found"
    }

def test_update_missing_card_returns_404():
    """Updating a nonexistent card should return a consisten 404 response."""

    response = client.patch(
        "/cards/999999",
        json = {"price" : 15.00}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail" : "Card not Found"
    }