import os
import httpx
import pytest

from datetime import datetime, timedelta, timezone
import jwt

from fastapi.testclient import TestClient
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from decimal import Decimal


# Load backend/.env before reading TEST_DATABASE_URL.
import app.config


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "").strip()

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is required. Configure your cardfolio_test database."
    )

test_database_url = make_url(TEST_DATABASE_URL)

# These tests delete tables. Refuse any target outside our local test database.
if (
    test_database_url.drivername != "postgresql+psycopg"
    or test_database_url.database != "cardfolio_test"
    or test_database_url.host not in {"localhost", "127.0.0.1", "::1"}
    or test_database_url.query
):
    raise RuntimeError(
        "Tests require a local PostgreSQL database named cardfolio_test "
        "with no URL query parameters."
    )

# The application creates its engine during import, so select the test
# database before importing database.py or the FastAPI application.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.db.database import Base, get_db
from app.models.catalog_card import CatalogCard
from app.models.card_variant import CardVariant
from app.models.collection_item import CollectionItem
from app.models.price_snapshot import PriceSnapshot
from app.main import app
from app.routers import catalog as catalog_router
from app.services.tcgdex import TCGdexResponseError
from app.services.catalog_import import import_catalog_card
from app.schemas.catalog import(
    CatalogCardSearchResult,
    CatalogVariantSearchResult
)
from app.models.user import User
from app.security import password_hasher

# Use the dedicated PostgreSQL database validated above.
test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = test_engine
)

@pytest.fixture(autouse=True)
def reset_test_database():
    """Give each test fresh tables in the dedicated test database."""

    # Check the actual connection before allowing any table deletion.
    with test_engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    if database_name != "cardfolio_test":
        raise RuntimeError("Refusing to clear a database other than cardfolio_test.")

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    try:
        yield
    finally:
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

def test_legacy_card_routes_are_not_exposed():
    """The public app no longer serves the old standalone card endpoints."""
    for method, path in (
        ("GET", "/cards"),
        ("POST", "/cards"),
        ("GET", "/cards/1"),
        ("PATCH", "/cards/1"),
        ("DELETE", "/cards/1"),
    ):
        response = client.request(method, path)
        assert response.status_code == 404, f"{method} {path} is still exposed"


# A duplicate provider identity violates a database constraint, which
# SQLAlchemy reports as IntegrityError even when no HTTP request is involved.
def test_catalog_card_rejects_duplicate_provider_identity():
    """
    A provider card may be imported only once into the catalog.
    """
    first_card = CatalogCard(
        provider="tcgdex",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
    )

    duplicate_card = CatalogCard(
        provider="tcgdex",
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
        provider="tcgdex",
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

def test_collection_item_can_be_saved(auth_account):

    first_card = CatalogCard(
        provider="tcgdex",
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
        user_id = auth_account["id"],
        condition = "near_mint"
    )
    with TestingSessionLocal() as db:
            
            db.add(collection_item)
            db.commit()
            db.refresh(collection_item)
            
            assert collection_item.id is not None
            assert collection_item.card_variant_id == first_variant.id
            assert collection_item.user_id == auth_account["id"]
            assert collection_item.quantity == 1
            assert collection_item.purchase_currency == "USD"

def test_collection_item_rejects_invalid_condition(auth_account):
    first_card = CatalogCard(
        provider="tcgdex",
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
        user_id = auth_account["id"],
        condition = "perfect"
    )

    with TestingSessionLocal() as db:
        db.add(collection_item)
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()

        db.rollback()
        # Verify this failed for the condition, rather than missing ownership.
        assert exc_info.value.orig.diag.constraint_name == "ck_collection_items_condition_allowed"


@pytest.fixture
def collection_variant_id():
    catalog_card = CatalogCard(
        provider="tcgdex",
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

    return variant_id


def test_create_collection_item_endpoint(auth_account, auth_headers, collection_variant_id):
    response = client.post(
        "/collection-items",
        headers=auth_headers,
        json = {
            "card_variant_id": collection_variant_id,
            "condition" : "near_mint",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["card_variant_id"] == collection_variant_id
    assert data["condition"] == "near_mint"
    assert data["quantity"] == 1
    assert data["purchase_currency"] == "USD"

    with TestingSessionLocal() as db:
        assert db.get(CollectionItem, data["id"]).user_id == auth_account["id"]


def test_get_collection_items_paginates_in_id_order(auth_headers):
    catalog_card = CatalogCard(
        provider="tcgdex",
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
        headers=auth_headers,
        json={
            "card_variant_id": variant_id,
            "condition": "near_mint",
        },
    )

    second_response = client.post(
        "/collection-items",
        headers=auth_headers,
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
        headers=auth_headers,
        params={"limit": 1},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    # ID ordering means the first created item should be returned first.
    assert data[0]["id"] == first_response.json()["id"]
    assert data[0]["condition"] == "near_mint"

    next_page = client.get(
        "/collection-items",
        headers=auth_headers,
        params={"limit": 1, "offset": 1},
    )
    assert next_page.status_code == 200
    assert [item["id"] for item in next_page.json()] == [second_response.json()["id"]]

    # Reaching the end of a collection returns an empty page.
    last_page = client.get(
        "/collection-items",
        headers=auth_headers,
        params={"limit": 1, "offset": 2},
    )
    assert last_page.status_code == 200
    assert last_page.json() == []


def test_get_collection_items_rejects_negative_offset(auth_headers):
    response = client.get(
        "/collection-items", headers=auth_headers, params={"offset": -1}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "offset"]


def test_update_collection_item_changes_only_supplied_fields(auth_headers):
    catalog_card = CatalogCard(
        provider="tcgdex",
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
        headers=auth_headers,
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
        headers=auth_headers,
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

def test_delete_collection_item_removes_item_but_preserves_variant(auth_headers):
    catalog_card = CatalogCard(
        provider="tcgdex",
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
        headers=auth_headers,
        json={
            "card_variant_id": variant_id,
            "condition": "near_mint",
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/collection-items/{item_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    # A 204 response should contain no response body.
    assert delete_response.content == b""

    with TestingSessionLocal() as db:
        # The owned item should be gone.
        assert db.get(CollectionItem, item_id) is None

        # The shared variant must remain for other collection items.
        assert db.get(CardVariant, variant_id) is not None

@pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
def test_collection_routes_require_authentication(
    auth_account, auth_headers, collection_variant_id, method
):
    created = client.post(
        "/collection-items",
        headers=auth_headers,
        json={"card_variant_id": collection_variant_id, "condition": "near_mint"},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    path = "/collection-items"
    payload = None
    if method == "POST":
        payload = {"card_variant_id": collection_variant_id, "condition": "near_mint"}
    elif method in {"PATCH", "DELETE"}:
        path = f"/collection-items/{item_id}"
        if method == "PATCH":
            payload = {"quantity": 99}

    response = client.request(method, path, json=payload)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    # Rejected creation, updates, and deletion must leave the data untouched.
    with TestingSessionLocal() as db:
        saved_items = db.query(CollectionItem).all()
        assert len(saved_items) == 1
        assert saved_items[0].id == item_id
        assert saved_items[0].quantity == 1
        assert saved_items[0].user_id == auth_account["id"]


def test_collection_items_are_private_between_users(auth_headers, collection_variant_id):
    registration = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "another-practice-passphrase"},
    )
    assert registration.status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": "other@example.com", "password": "another-practice-passphrase"},
    )
    assert login.status_code == 200
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    payload = {"card_variant_id": collection_variant_id, "condition": "near_mint"}

    first = client.post("/collection-items", headers=auth_headers, json=payload)
    assert first.status_code == 201
    first_id = first.json()["id"]

    # A new account sees an empty collection even when another account has items.
    empty = client.get("/collection-items", headers=other_headers)
    assert empty.status_code == 200
    assert empty.json() == []

    # Both accounts can own the same shared card variant as separate items.
    second = client.post("/collection-items", headers=other_headers, json=payload)
    assert second.status_code == 201
    second_id = second.json()["id"]
    assert first_id != second_id

    for headers, own_id, foreign_id in (
        (auth_headers, first_id, second_id),
        (other_headers, second_id, first_id),
    ):
        listing = client.get("/collection-items", headers=headers, params={"limit": 1})
        assert listing.status_code == 200
        assert [item["id"] for item in listing.json()] == [own_id]

        # Each account has one item; another account's row cannot fill page two.
        next_page = client.get(
            "/collection-items", headers=headers, params={"limit": 1, "offset": 1}
        )
        assert next_page.status_code == 200
        assert next_page.json() == []

        update = client.patch(
            f"/collection-items/{foreign_id}", headers=headers, json={"quantity": 99}
        )
        assert update.status_code == 404
        assert update.json() == {"detail": "Collection item not found"}

        deletion = client.delete(f"/collection-items/{foreign_id}", headers=headers)
        assert deletion.status_code == 404
        assert deletion.json() == {"detail": "Collection item not found"}

    with TestingSessionLocal() as db:
        assert db.get(CollectionItem, first_id).quantity == 1
        assert db.get(CollectionItem, second_id).quantity == 1

    # Deleting one's own copy must preserve the other account's copy and its card.
    deletion = client.delete(f"/collection-items/{first_id}", headers=auth_headers)
    assert deletion.status_code == 204
    remaining = client.get("/collection-items", headers=other_headers)
    assert remaining.status_code == 200
    assert [item["id"] for item in remaining.json()] == [second_id]
    assert remaining.json()[0]["card_variant_id"] == collection_variant_id


def test_collection_item_owner_cannot_be_set_or_changed_by_client(
    auth_account, auth_headers, collection_variant_id
):
    registration = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "another-practice-passphrase"},
    )
    assert registration.status_code == 201
    other_user_id = registration.json()["id"]

    created = client.post(
        "/collection-items",
        headers=auth_headers,
        json={
            "card_variant_id": collection_variant_id,
            "condition": "near_mint",
            "user_id": other_user_id,
        },
    )
    # Extra creation fields are ignored; the authenticated account remains the owner.
    assert created.status_code == 201
    item_id = created.json()["id"]

    transfer = client.patch(
        f"/collection-items/{item_id}",
        headers=auth_headers,
        json={"user_id": other_user_id},
    )
    assert transfer.status_code == 422
    with TestingSessionLocal() as db:
        assert db.get(CollectionItem, item_id).user_id == auth_account["id"]
        assert db.query(CollectionItem).filter_by(user_id=other_user_id).count() == 0


def test_price_snapshot_can_be_saved():
    """Save a variant price observation and check what should be its auto defaults."""
    catalog_card = CatalogCard(
        provider="tcgdex",
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
    # Leave currency and observed_at unset so this test also checks their defaults.

    snapshot = PriceSnapshot(
        card_variant=variant,
        market_price=Decimal("25.50"),
        source="tcgplayer",
    )
    with TestingSessionLocal() as db:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        assert snapshot.id is not None
        assert snapshot.card_variant_id == variant.id
        assert snapshot.market_price == Decimal("25.50")
        assert snapshot.currency == "USD"
        assert snapshot.source == "tcgplayer"
        assert snapshot.observed_at is not None
        assert snapshot in variant.price_snapshots    

def test_price_snapshot_rejects_negative_market_price():
    """Reject negative historical prices at the database boundary."""
    catalog_card = CatalogCard(
        provider="tcgdex",
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

    snapshot = PriceSnapshot(
        card_variant=variant,
        market_price=Decimal("-0.01"),
        source="tcgplayer",
    )

    with TestingSessionLocal() as db:
        db.add(snapshot)

        # The database constraint should reject this even without API validation.
        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()


def test_deleting_card_variant_removes_price_snapshots():
    """Delete a variant's price history while preserving its catalog card."""
    catalog_card = CatalogCard(
        provider="tcgdex",
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

    snapshot = PriceSnapshot(
        card_variant=variant,
        market_price=Decimal("25.50"),
        source="tcgplayer",
    )

    with TestingSessionLocal() as db:
        db.add(snapshot)
        db.commit()

        catalog_card_id = catalog_card.id
        variant_id = variant.id
        snapshot_id = snapshot.id

    # Use a fresh session so the database handles the ON DELETE CASCADE.
    with TestingSessionLocal() as db:
        variant_to_delete = db.get(CardVariant, variant_id)

        assert variant_to_delete is not None

        db.delete(variant_to_delete)
        db.commit()

    with TestingSessionLocal() as db:
        assert db.get(CardVariant, variant_id) is None
        assert db.get(PriceSnapshot, snapshot_id) is None

        # Deleting one finish must not remove its shared catalog card.
        assert db.get(CatalogCard, catalog_card_id) is not None


def test_catalog_search_returns_504_when_provider_times_out(
    monkeypatch,
):
    """Return a gateway timeout when the external provider is too slow."""

    request = httpx.Request(
        "GET",
        "https://api.tcgdex.net/v2/en/cards",
    )

    def fail_search(**kwargs):
        raise httpx.ReadTimeout(
            "Provider timed out",
            request=request,
        )

    monkeypatch.setattr(
        catalog_router,
        "search_tcgdex_cards",
        fail_search,
    )

    response = client.get(
        "/catalog/search",
        params={"query": "Pikachu"},
    )

    assert response.status_code == 504
    assert response.json() == {
        "detail": (
            "The card catalog provider took too long to respond."
        )
    }


def test_catalog_search_returns_502_when_provider_fails(
    monkeypatch,
):
    """Return a gateway error when the provider cannot be reached."""

    request = httpx.Request(
        "GET",
        "https://api.tcgdex.net/v2/en/cards",
    )

    def fail_search(**kwargs):
        raise httpx.ConnectError(
            "Unable to connect to provider",
            request=request,
        )

    monkeypatch.setattr(
        catalog_router,
        "search_tcgdex_cards",
        fail_search,
    )

    response = client.get(
        "/catalog/search",
        params={"query": "Pikachu"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": (
            "The card catalog provider is currently unavailable."
        )
    }

def test_catalog_search_rejects_blank_query(
    monkeypatch,
):
    """
    Reject a search containing spaces but no actual card name.
    """

    def fail_if_called(**kwargs):
        pytest.fail(
            "The provider should not be called for an empty search."
        )

    monkeypatch.setattr(
        catalog_router,
        "search_tcgdex_cards",
        fail_if_called,
    )

    response = client.get(
        "/catalog/search",
        params={"query": "   "},
    )

    assert response.status_code == 422

def test_catalog_search_returns_502_for_invalid_provider_response(monkeypatch):
    """Return a gateway error when the service reports unusable provider data."""

    def fail_search(**kwargs):
        """Simulate the service rejecting the provider's response."""
        raise TCGdexResponseError("Invalid test response")

    # Replace the function where the router uses it; no real API call is needed.
    monkeypatch.setattr(
        catalog_router,
        "search_tcgdex_cards",
        fail_search,
    )

    response = client.get(
        "/catalog/search",
        params={"query": "Pikachu"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The card catalog provider returned an invalid response."
    }

@pytest.mark.parametrize("method,path,payload", [
    (
        "POST",
        "/collection-items",
        {
            "card_variant_id": 1,
            "condition": "near_mint",
            "quantity": 2_147_483_648,
        },
    ),
    (
        "PATCH",
        "/collection-items/1",
        {"quantity": 2_147_483_648},
    ),
])
def test_collection_item_rejects_quantity_overflow(method, path, payload, auth_headers):
    response = client.request(method, path, json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "quantity"]
        for error in response.json()["detail"]
    )

def test_import_catalog_card_saves_new_card():
    provider_card = CatalogCardSearchResult(
        provider="tcgdex",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
        variants=[
            CatalogVariantSearchResult(
                variant_key="holofoil",
                market_price=Decimal("25.50"),
            ),
            CatalogVariantSearchResult(
                variant_key="normal",
                market_price=None,
            ),
        ],
    )

    # Import the card and remember its database ID.
    with TestingSessionLocal() as db:
        imported_card = import_catalog_card(db, provider_card)
        card_id = imported_card.id

    # Open another session to verify the records were committed.
    with TestingSessionLocal() as db:
        saved_card = db.query(CatalogCard).one()

        assert saved_card.id == card_id
        assert saved_card.provider == "tcgdex"
        assert saved_card.provider_card_id == "base1-4"
        assert saved_card.name == "Charizard"

        variants = {
            variant.variant_key: variant
            for variant in saved_card.variants
        }

        assert set(variants) == {"holofoil", "normal"}
        assert variants["holofoil"].market_price == Decimal("25.50")
        assert variants["holofoil"].market_price_source == "tcgplayer"
        assert variants["normal"].market_price is None

        snapshot = db.query(PriceSnapshot).one()

        assert snapshot.card_variant_id == variants["holofoil"].id
        assert snapshot.market_price == Decimal("25.50")
        assert snapshot.currency == "USD"
        assert snapshot.source == "tcgplayer"
        assert snapshot.observed_at is not None
        assert (
            snapshot.observed_at
            == variants["holofoil"].market_price_updated_at
        )

def test_import_catalog_card_reuses_existing_records():
    provider_card = CatalogCardSearchResult(
        provider="tcgdex",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
        variants=[
            CatalogVariantSearchResult(
                variant_key="holofoil",
                market_price=Decimal("25.50"),
            ),
        ],
    )

    # First import: save the IDs of the created records.
    with TestingSessionLocal() as db:
        first_card = import_catalog_card(db, provider_card)

        card_id = first_card.id
        variant = db.query(CardVariant).one()
        snapshot = db.query(PriceSnapshot).one()
        variant_id = variant.id
        snapshot_id = snapshot.id

        # An older observation lets us check freshness without sleeps or timing races.
        previous_observation = datetime(2020, 1, 1, tzinfo=timezone.utc)
        variant.market_price_updated_at = previous_observation
        snapshot.observed_at = previous_observation
        db.commit()

    # Import the same provider card through a fresh session.
    with TestingSessionLocal() as db:
        second_card = import_catalog_card(db, provider_card)

        assert second_card.id == card_id

    # The price was checked again, but unchanged quotes don't duplicate history.
    with TestingSessionLocal() as db:
        assert db.query(CatalogCard).one().id == card_id
        variant = db.query(CardVariant).one()
        snapshot = db.query(PriceSnapshot).one()
        assert variant.id == variant_id
        assert variant.market_price == Decimal("25.50")
        assert variant.market_price_updated_at > previous_observation
        assert snapshot.id == snapshot_id
        assert snapshot.observed_at == previous_observation


@pytest.fixture
def priced_provider_card():
    return CatalogCardSearchResult(
        provider="tcgdex",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
        variants=[
            CatalogVariantSearchResult(
                variant_key="holofoil", market_price=Decimal("25.50")
            )
        ],
    )


@pytest.mark.parametrize(
    "initial_price,new_price",
    [
        (Decimal("25.50"), Decimal("30.00")),
        (Decimal("25.50"), Decimal("0.00")),
        (None, Decimal("25.50")),
    ],
)
def test_reimport_updates_price_and_preserves_owned_items(
    auth_account, priced_provider_card, initial_price, new_price
):
    priced_provider_card.variants[0].market_price = initial_price
    with TestingSessionLocal() as db:
        card = import_catalog_card(db, priced_provider_card)
        card_id = card.id
        variant_id = db.query(CardVariant).one().id
        owned_item = CollectionItem(
            user_id=auth_account["id"],
            card_variant_id=variant_id,
            condition="lightly_played",
            quantity=2,
            purchase_price_per_card=Decimal("12.34"),
            notes="Keep the original purchase details",
        )
        db.add(owned_item)
        db.commit()
        item_id = owned_item.id
        history_before = [
            (row.id, row.market_price, row.currency, row.source, row.observed_at)
            for row in db.query(PriceSnapshot).order_by(PriceSnapshot.id).all()
        ]

    priced_provider_card.variants[0].market_price = new_price
    with TestingSessionLocal() as db:
        assert import_catalog_card(db, priced_provider_card).id == card_id

    with TestingSessionLocal() as db:
        variant = db.query(CardVariant).one()
        assert variant.id == variant_id
        assert variant.market_price == new_price
        assert variant.currency == "USD"
        assert variant.market_price_source == "tcgplayer"

        history = db.query(PriceSnapshot).order_by(PriceSnapshot.id).all()
        assert len(history) == len(history_before) + 1
        assert [
            (row.id, row.market_price, row.currency, row.source, row.observed_at)
            for row in history[:-1]
        ] == history_before
        assert history[-1].card_variant_id == variant_id
        assert history[-1].market_price == new_price
        assert history[-1].observed_at == variant.market_price_updated_at

        # A price refresh must keep existing ownership and purchase data intact.
        owned_item = db.get(CollectionItem, item_id)
        assert owned_item.user_id == auth_account["id"]
        assert owned_item.card_variant_id == variant_id
        assert owned_item.condition == "lightly_played"
        assert owned_item.quantity == 2
        assert owned_item.purchase_price_per_card == Decimal("12.34")
        assert owned_item.notes == "Keep the original purchase details"


def test_reimport_missing_price_preserves_last_known_quote(priced_provider_card):
    with TestingSessionLocal() as db:
        import_catalog_card(db, priced_provider_card)
        variant = db.query(CardVariant).one()
        previous_quote = (
            variant.market_price,
            variant.currency,
            variant.market_price_source,
            variant.market_price_updated_at,
        )
        snapshot_id = db.query(PriceSnapshot).one().id

    incoming = priced_provider_card.variants[0]
    incoming.market_price = None
    incoming.currency = "EUR"
    incoming.variant_name = "Updated label"
    with TestingSessionLocal() as db:
        import_catalog_card(db, priced_provider_card)

    with TestingSessionLocal() as db:
        variant = db.query(CardVariant).one()
        assert (
            variant.market_price,
            variant.currency,
            variant.market_price_source,
            variant.market_price_updated_at,
        ) == previous_quote
        assert variant.variant_name == "Updated label"
        assert db.query(PriceSnapshot).one().id == snapshot_id


def test_import_catalog_endpoint_saves_card_and_returns_variant_ids(monkeypatch):
    provider_card = CatalogCardSearchResult(
        provider="tcgdex",
        provider_card_id="base1-4",
        name="Charizard",
        set_id="base1",
        set_name="Base",
        card_number="4",
        variants=[
            CatalogVariantSearchResult(
                variant_key="holofoil",
                market_price=Decimal("25.50"),
            ),
        ],
    )

    def fake_get_tcgdex_card(provider_card_id):
        assert provider_card_id == "base1-4"
        return provider_card

    # Replace the provider lookup where the router uses it. The HTTP route,
    # response serialization, and PostgreSQL persistence still run normally.
    monkeypatch.setattr(
        catalog_router,
        "get_tcgdex_card",
        fake_get_tcgdex_card,
    )

    response = client.post(
        "/catalog/import",
        json={"provider_card_id": "base1-4"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["provider_card_id"] == "base1-4"
    assert body["name"] == "Charizard"
    assert len(body["variants"]) == 1

    returned_variant = body["variants"][0]
    assert returned_variant["variant_key"] == "holofoil"
    assert Decimal(returned_variant["market_price"]) == Decimal("25.50")
    assert returned_variant["currency"] == "USD"

    # A separate session confirms that the returned IDs belong to committed
    # records, including the variant a collection item will reference.
    with TestingSessionLocal() as db:
        saved_card = db.query(CatalogCard).one()
        saved_variant = db.query(CardVariant).one()
        snapshot = db.query(PriceSnapshot).one()

        assert body["id"] == saved_card.id
        assert returned_variant["id"] == saved_variant.id
        assert saved_variant.catalog_card_id == saved_card.id
        assert snapshot.card_variant_id == saved_variant.id
        assert snapshot.market_price == Decimal("25.50")

def test_register_user_saves_hash_and_returns_safe_response():
    password = "local-practice-passphrase"

    response = client.post(
        "/auth/register",
        json={
            "email": "Learner@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "learner@example.com"
    assert set(body) == {"id", "email", "created_at"}

    # Check the saved record, not just the HTTP response.
    with TestingSessionLocal() as db:
        user = db.query(User).one()

        assert user.id == body["id"]
        assert user.email == "learner@example.com"
        assert user.password_hash != password
        assert password_hasher.verify(password, user.password_hash)


def test_register_user_rejects_duplicate_email():
    first_response = client.post(
        "/auth/register",
        json={
            "email": "Learner@example.com",
            "password": "local-practice-passphrase",
        },
    )
    assert first_response.status_code == 201

    # Different capitalization must not create a second account.
    duplicate_response = client.post(
        "/auth/register",
        json={
            "email": "learner@example.com",
            "password": "another-practice-passphrase",
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "An account with this email already exists."
    }

    with TestingSessionLocal() as db:
        assert db.query(User).count() == 1


@pytest.fixture
def auth_account(monkeypatch):
    # Tests use their own signing key, never the secret in your local .env.
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-only-signing-key-not-for-production-123456",
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "learner@example.com",
            "password": "local-practice-passphrase",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(auth_account):
    """Use the real login route so collection tests exercise token validation."""
    response = client.post(
        "/auth/login",
        json={
            "email": auth_account["email"],
            "password": "local-practice-passphrase",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_token_identifies_current_user(auth_account):
    response = client.post(
        "/auth/login",
        json={
            "email": "LEARNER@example.com",
            "password": "local-practice-passphrase",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"

    # Use the actual login token to exercise signature checking and user lookup.
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == auth_account


@pytest.mark.parametrize(
    "email,password",
    [
        ("learner@example.com", "incorrect-password"),
        ("unknown@example.com", "local-practice-passphrase"),
    ],
)
def test_login_rejects_invalid_credentials(auth_account, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Incorrect email or password."
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "case",
    ["missing", "malformed", "expired", "wrong_signature", "missing_expiry"],
)
def test_me_rejects_invalid_authentication(auth_account, case):
    headers = {}

    if case == "malformed":
        headers["Authorization"] = "Bearer not-a-valid-token"

    elif case != "missing":
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(auth_account["id"]),
            "iat": now - timedelta(minutes=2),
            "exp": now + timedelta(minutes=5),
        }
        signing_key = os.environ["JWT_SECRET_KEY"]

        if case == "expired":
            # Create an already-expired token; no waiting or sleeping needed.
            payload["exp"] = now - timedelta(minutes=1)
        elif case == "wrong_signature":
            signing_key = "different-test-signing-key-1234567890123456"
        elif case == "missing_expiry":
            del payload["exp"]

        token = jwt.encode(payload, signing_key, algorithm="HS256")
        headers["Authorization"] = f"Bearer {token}"

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {
        "detail": "Invalid or expired authentication token."
    }
