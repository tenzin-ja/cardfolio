# Cardfolio

Cardfolio is a trading card collection and portfolio tracker. The
project is currently focused on building a reliable backend API for storing and
managing card data before the frontend is added.

## Current Status

The backend currently supports:

- Creating cards with a name, rarity, condition, and price
- Retrieving saved cards
- Filtering cards by a partial, case-insensitive name match
- Limiting list results from 1 to 100 cards
- Partially updating an existing card
- Deleting a card
- Validating request and response data with Pydantic
- Persisting card data in PostgreSQL through SQLAlchemy and Psycopg
- Testing API behavior with pytest and a dedicated PostgreSQL database

## Tech Stack

- **API:** FastAPI
- **Database:** PostgreSQL 18
- **ORM:** SQLAlchemy
- **Database driver:** Psycopg 3
- **Validation:** Pydantic
- **Testing:** pytest, FastAPI TestClient, and HTTPX

## Project Structure

```text
cardfolio/
├── backend/
│   ├── app/
│   │   ├── db/          # Database connection and sessions
│   │   ├── models/      # SQLAlchemy database models
│   │   ├── routers/     # Card API routes
│   │   ├── schemas/     # Pydantic request and response schemas
│   │   └── main.py      # FastAPI application entry point
│   ├── tests/           # API tests
│   └── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Check whether the backend is running |
| `POST` | `/cards` | Create and save a card |
| `GET` | `/cards` | Retrieve cards with optional `name` and `limit` parameters |
| `PATCH` | `/cards/{card_id}` | Update only the provided fields of a card |
| `DELETE` | `/cards/{card_id}` | Delete a card |

Example request:

```json
{
  "name": "Pikachu",
  "rarity": "Rare",
  "condition": "Near Mint",
  "price": 25.50
}
```

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
Pokémon TCG API key and the database password:

```dotenv
POKEMON_TCG_API_KEY=replace-with-your-key
DATABASE_URL=postgresql+psycopg://cardfolio_app:ENCODED_PASSWORD@localhost:5432/cardfolio
TEST_DATABASE_URL=postgresql+psycopg://cardfolio_app:ENCODED_PASSWORD@localhost:5432/cardfolio_test
```

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
check. Provider tests use mocked HTTP responses and do not consume API quota.

The latest reported run passed all 38 tests, covering card and collection APIs,
database constraints, price snapshots, provider mapping, and error handling.

## Roadmap

- Expand tests for filtering, deletion, and error responses
- Add full pagination for larger collections
- Integrate external Pokémon card data and search
- Build the collection dashboard and frontend
- Add user accounts and authentication
- Deploy the backend with PostgreSQL
