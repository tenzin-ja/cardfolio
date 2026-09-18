# Cardfolio

Cardfolio is a trading card collection and portfolio tracker. The
project is currently focused on building a reliable backend API for storing and
managing card data before the frontend is added.

## Current Status

As of September 18, 2026, the project is in backend development. The frontend
has not been started.

- [x] PostgreSQL persistence with SQLAlchemy, Psycopg, and Alembic migrations
- [x] Pokémon card search and single-card lookup through TCGdex
- [x] Importing catalog cards and variants, with existing records reused on reimport
- [x] Creating, listing, updating, and deleting collection items
- [x] Collection responses with card name, set, image, readable variant name,
  stored market price, and currency
- [x] Initial price snapshots for newly imported variants with available prices
- [x] User registration with normalized emails, Argon2 password hashing, and
  duplicate-email rejection
- [x] Login with 30-minute JWT access tokens and authenticated `/auth/me`
- [x] Tests for registration, login, invalid tokens, collection operations,
  provider mapping, and database behavior
- [ ] Per-user collection ownership and access restrictions

**Collection ownership is the next planned milestone and has not been
implemented.** Collection items currently have no `user_id`, and collection,
catalog, and legacy card routes do not require authentication. `/auth/me` is
protected; signing in does not yet make collections private. The backend is
not ready for public multi-user use.

Market prices are stored values, not live valuations on every collection
request. Reimporting can update variant names, but it does not refresh prices
or add new price snapshots for existing variants. Missing prices remain `null`.

## Tech Stack

- **API:** FastAPI
- **Database:** PostgreSQL 18
- **ORM:** SQLAlchemy
- **Database driver:** Psycopg 3
- **Migrations:** Alembic
- **Validation:** Pydantic
- **Catalog provider:** TCGdex through HTTPX
- **Authentication:** pwdlib with Argon2 and PyJWT
- **Testing:** pytest, FastAPI TestClient, and HTTPX

## Project Structure

```text
cardfolio/
├── backend/
│   ├── app/
│   │   ├── db/          # Database connection and sessions
│   │   ├── models/      # SQLAlchemy database models
│   │   ├── routers/     # Auth, catalog, collection, and legacy card routes
│   │   ├── schemas/     # Pydantic request and response schemas
│   │   ├── services/    # TCGdex integration and catalog import logic
│   │   ├── config.py    # Environment-based configuration
│   │   ├── dependencies.py # Token validation and current-user lookup
│   │   ├── security.py  # Password hashing and access-token creation
│   │   └── main.py      # FastAPI application entry point
│   ├── migrations/      # Alembic schema history
│   ├── tests/           # API, provider, and configuration tests
│   └── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Check whether the backend is running |
| `POST` | `/auth/register` | Register an account using email and password |
| `POST` | `/auth/login` | Verify credentials and return a bearer access token |
| `GET` | `/auth/me` | Return the account identified by a valid bearer token |
| `GET` | `/catalog/search` | Search TCGdex with `query`, `page`, and `page_size` |
| `POST` | `/catalog/import` | Import a provider card and return local card and variant IDs |
| `POST` | `/collection-items` | Save an owned copy using a local `card_variant_id` |
| `GET` | `/collection-items` | List collection items with related card details and optional `limit` |
| `PATCH` | `/collection-items/{item_id}` | Update condition, quantity, purchase information, or notes |
| `DELETE` | `/collection-items/{item_id}` | Delete a collection item while preserving its catalog card and variant |
| `POST` | `/cards` | Create a legacy standalone card record |
| `GET` | `/cards` | List legacy cards with optional `name` and `limit` parameters |
| `GET` | `/cards/{card_id}` | Retrieve one legacy card |
| `PATCH` | `/cards/{card_id}` | Update a legacy card |
| `DELETE` | `/cards/{card_id}` | Delete a legacy card |

The `/cards` routes are the earlier standalone-card workflow. The catalog and
collection routes are the workflow intended for the frontend; a decision about
retiring or restricting `/cards` is still pending.

Catalog search returns lightweight summaries. Import a selected card to obtain
its variants and their local database IDs. For example, send this body to
`POST /catalog/import`:

```json
{
  "provider_card_id": "base1-4"
}
```

Then use an `id` from the returned `variants` list as `card_variant_id` in
`POST /collection-items`. That is a local variant ID, distinct from the
provider's card ID and opaque variant key. Collection responses nest variant
information under `card_variant` and card details under
`card_variant.catalog_card`.

Collection listing currently returns up to 20 items by default, with a maximum
`limit` of 100. It does not yet support requesting subsequent pages. Catalog
search supports pages, but its `total_count` is `null` because the provider
response does not supply a total.

## Running the Backend

### 1. Clone the repository

```bash
git clone https://github.com/tenzin-ja/cardfolio.git
cd cardfolio/backend
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL and local settings

Install PostgreSQL and start its local service. In `psql`, connect as the
`postgres` administrator and create the application login:

```sql
CREATE ROLE cardfolio_app WITH LOGIN;
```

Set the login password using the interactive prompt:

```text
\password cardfolio_app
```

Then create the development and test databases:

```sql
CREATE DATABASE cardfolio OWNER cardfolio_app;
CREATE DATABASE cardfolio_test OWNER cardfolio_app;
```

These are one-time setup commands. Reuse the existing login and databases if
you have already created them.

Create `backend/.env` using `backend/.env.example` as a template. Fill in the
database password in both database URLs. Catalog requests use TCGdex and do
not require an API key.

```dotenv
DATABASE_URL=postgresql+psycopg://cardfolio_app:ENCODED_PASSWORD@localhost:5432/cardfolio
TEST_DATABASE_URL=postgresql+psycopg://cardfolio_app:ENCODED_PASSWORD@localhost:5432/cardfolio_test
# Paste a locally generated random signing key here.
JWT_SECRET_KEY=
```

With the virtual environment active, generate the signing key locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output into `JWT_SECRET_KEY` in your ignored `.env` file. The application
requires at least 32 bytes for this secret; use the generated random value.
Keep it stable between restarts. Changing the key invalidates previously issued
tokens. Never commit the real key or database password.

URL-encode the password portion if it contains reserved characters such as
`@`, `/`, or `%`. Keep real credentials in the Git-ignored `.env`; the committed
`.env.example` must contain placeholders only. Existing environment variables
take precedence over `.env`. The application requires `DATABASE_URL` and has
no default database fallback.

### 5. Apply database migrations

From `backend`, with the virtual environment active:

```bash
python -m alembic upgrade head
```

This creates or updates the tables in the database selected by `DATABASE_URL`.
It does not copy data from a previous database.

### 6. Start the development server

```bash
python -m uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`. Interactive API documentation is
available at `http://127.0.0.1:8000/docs`.

To check authentication in Swagger:

1. Register through `/auth/register` using an email and a password of 15–128
   characters. Registration returns account details without the password hash.
2. Submit the same credentials to `/auth/login` and copy the `access_token`.
3. Click **Authorize** and paste only the token; Swagger supplies the `Bearer`
   prefix.
4. Execute `/auth/me` to retrieve the signed-in account.

Tokens expire after 30 minutes. Refresh tokens and server-side logout/revocation
are not implemented. Clearing authorization in Swagger only removes its local
token. The collection routes still operate without user ownership, as described
in Current Status.

## Running the Tests

Start PostgreSQL and configure `TEST_DATABASE_URL` as described above. From
the `backend` directory with the virtual environment active:

```bash
python -m pytest
```

The database tests create and drop application tables in `cardfolio_test` for
each test. Use this database only for disposable test data. The setup checks
the URL and actual database name before clearing tables; it accepts only a
local `postgresql+psycopg` URL for `cardfolio_test`, with no query parameters.
Run the suite sequentially, without parallel test workers.

The fixture creates test tables from SQLAlchemy models, so it does not require
running Alembic against the test database. Migration verification is a separate
check. Provider tests use mocked HTTP responses rather than contacting TCGdex.
Login/token tests supply a test-only signing key through environment overrides.

The suite covers card and collection APIs, database constraints, price snapshots,
catalog import/reimport behavior, provider mapping, registration, password-hash
storage, login, and token rejection. Run the command above for the current test
result; no fixed test count is maintained here.

## Roadmap

Before starting the frontend:

1. Add per-user collection ownership: choose an owner for existing development
   items, migrate the data, and require a valid user for each collection item.
2. Require authentication for collection operations, assign ownership from the
   signed-in user, and verify that users cannot read or modify each other's items.
3. Add collection pagination and configure CORS for the frontend.
4. Decide access rules for catalog search/import and retire or restrict the
   legacy `/cards` endpoints.
5. Verify the complete workflow and update setup documentation, then begin the
   collection dashboard and frontend.

Before public release: deployment with PostgreSQL, CI, security and operational
checks, account recovery, and abuse protection.

Deferred beyond the initial frontend: AI assistant/MCP integration, scheduled
price refreshes, price-history charts, analytics, and additional card providers.
