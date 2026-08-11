import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

#The application engine is created while app modules are imported, so this 
#override must be set before impoting the database or FastApi application
os.environ["DATABASE_URL"] = "sqlite://"

from app.db.database import Base, get_db
from app.models.catalog_card import CatalogCard
from app.models.card_variant import CardVariant
from app.models.collection_item import CollectionItem

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

def test_get_card_by_id():
    """Retrieve the exact card matching the requested ID."""
    create_response = client.post(
        "/cards",
        json={"name": "Eevee"}
    )
    assert create_response.status_code == 200

    card_id = create_response.json()["id"]
    response = client.get(f"/cards/{card_id}")

    assert response.status_code == 200
    assert response.json()["id"] == card_id
    assert response.json()["name"] == "Eevee"


def test_get_missing_card_returns_404():
    """Return 404 when the requested card ID does not exist."""
    response = client.get("/cards/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Card not found"
    }

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

def test_update_card_rejects_null_name():
    """A PATCH may omit the name, but it cannot explicitly erase the name."""

    create_response = client.post(
        "/cards",
        json={"name": "Pikachu"}
    )

    assert create_response.status_code == 200

    card_id = create_response.json()["id"]

    response = client.patch(
        f"/cards/{card_id}",
        json={"name": None}
    )

    assert response.status_code == 422

    # Confirm that the rejected update did not alter the saved card.
    get_response = client.get("/cards")
    assert get_response.json()[0]["name"] == "Pikachu"

#Testing database rule. Checking SQlite doesn't return a http response when noticing a duplicate.
#Sqlalchemy should raise integrityerror
def test_catalog_card_rejects_duplicate_provider_identity():
    """
    A provider card may be imported only once into the catalog.
    """
    first_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    duplicate_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard duplicate",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    with TestingSessionLocal() as db:
        db.add(first_card)
        db.commit()

        db.add(duplicate_card)

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()

#Testing card variant model. Verifying duplicate variants aren't possible
def test_card_variant_rejects_duplicate_variant_for_same_catalog_card():
    first_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    first_variant = CardVariant (
        catalog_card = first_card,
        variant_key = "holofoil"
    )

    with TestingSessionLocal() as db:
        db.add(first_card)
        db.commit()

        db.add(first_variant)
        db.commit()
        duplicate_variant = CardVariant(
        catalog_card = first_card,
        variant_key = "holofoil"
    )

        db.add(duplicate_variant)
        
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

#testing hook succesfully turns on foreignkey, and rejects variant with nonexistant id
def test_card_variant_rejects_missing_catalog_card():

       
    orphan_variant = CardVariant (
        catalog_card_id = 9999,
        variant_key = "holofoil"
    )
    with TestingSessionLocal() as db:

        db.add(orphan_variant)

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()    

def test_collection_item_can_be_saved():

    first_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    first_variant = CardVariant (
        catalog_card = first_card,
        variant_key = "holofoil"
    )

    collection_item = CollectionItem (
        card_variant = first_variant,
        condition = "near_mint"
    )
    with TestingSessionLocal() as db:
            
            db.add(collection_item)
            db.commit()
            db.refresh(collection_item)
            
            assert collection_item.id is not None
            assert collection_item.card_variant_id == first_variant.id
            assert collection_item.quantity == 1
            assert collection_item.purchase_currency == "USD"

def test_collection_item_rejects_invalid_condition():
    first_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    
    first_variant = CardVariant (
        catalog_card = first_card,
        variant_key = "holofoil"
    )

    collection_item = CollectionItem (
        card_variant = first_variant,
        condition = "perfect"
    )

    with TestingSessionLocal() as db:
        db.add(collection_item)
        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()


def test_create_collection_item_endpoint():
    catalog_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    variant = CardVariant(
        catalog_card=catalog_card,
        variant_key="holofoil",
    )
    with TestingSessionLocal() as db:
        #adding the variant also saves its connected Catalogcard
        db.add(variant)
        db.commit()
        db.refresh(variant)  
        #save the plain integer before the session closes. SQLAlehcmy objects 
        # may otherwise need their closed session to reload expired values
        variant_id = variant.id
    
        
    response = client.post(
        "/collection-items",
        json = {
            "card_variant_id": variant_id,
            "condition" : "near_mint",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["card_variant_id"] == variant_id
    assert data["condition"] == "near_mint"
    assert data["quantity"] == 1
    assert data["purchase_currency"] == "USD"


def test_get_collection_items_respects_limit_and_id_order():
    catalog_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    variant = CardVariant(
        catalog_card=catalog_card,
        variant_key="holofoil",
    )

    with TestingSessionLocal() as db:
        db.add(variant)
        db.commit()
        db.refresh(variant)

        variant_id = variant.id

    # Create two owned items through the real POST endpoint.
    first_response = client.post(
        "/collection-items",
        json={
            "card_variant_id": variant_id,
            "condition": "near_mint",
        },
    )

    second_response = client.post(
        "/collection-items",
        json={
            "card_variant_id": variant_id,
            "condition": "damaged",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    # Query parameters are supplied separately from a GET request body.
    response = client.get(
        "/collection-items",
        params={"limit": 1},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    # ID ordering means the first created item should be returned first.
    assert data[0]["id"] == first_response.json()["id"]
    assert data[0]["condition"] == "near_mint"


def test_update_collection_item_changes_only_supplied_fields():
    catalog_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    variant = CardVariant(
        catalog_card=catalog_card,
        variant_key="holofoil",
    )

    with TestingSessionLocal() as db:
        # Saving the variant also saves its connected CatalogCard.
        db.add(variant)
        db.commit()
        db.refresh(variant)

        # Store the integer before the database session closes.
        variant_id = variant.id

    # Create the collection item that will be updated.
    create_response = client.post(
        "/collection-items",
        json={
            "card_variant_id": variant_id,
            "condition": "near_mint",
            "quantity": 1,
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    # Send only quantity because PATCH should leave omitted fields unchanged.
    response = client.patch(
        f"/collection-items/{item_id}",
        json={
            "quantity": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == item_id
    assert data["quantity"] == 3

    # These fields were omitted from PATCH, so they should remain unchanged.
    assert data["condition"] == "near_mint"
    assert data["card_variant_id"] == variant_id

def test_delete_collection_item_removes_item_but_preserves_variant():
    catalog_card = CatalogCard(
        provider="pokemon_tcg",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    variant = CardVariant(
        catalog_card=catalog_card,
        variant_key="holofoil",
    )

    with TestingSessionLocal() as db:
        db.add(variant)
        db.commit()
        db.refresh(variant)

        variant_id = variant.id

    # Create the owned item that will be deleted.
    create_response = client.post(
        "/collection-items",
        json={
            "card_variant_id": variant_id,
            "condition": "near_mint",
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/collection-items/{item_id}"
    )

    assert delete_response.status_code == 204

    # A 204 response should contain no response body.
    assert delete_response.content == b""

    with TestingSessionLocal() as db:
        # The owned