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
- Persisting card data in SQLite through SQLAlchemy
- Testing API behavior with pytest and an isolated in-memory database

## Tech Stack

- **API:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Testing:** pytest, FastAPI TestClient, and HTTPX

## Project Structure

```text
cardfolio/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ db/          # Database connection and sessions
â”‚   â”‚   â”œâ”€â”€ models/      # SQLAlchemy database models
â”‚   â”‚   â”œâ”€â”€ routers/     # Card API routes
â”‚   â”‚   â”œâ”€â”€ schemas/     # Pydantic request and response schemas
â”‚   â”‚   â””â”€â”€ main.py      # FastAPI application entry point
â”‚   â”œâ”€â”€ tests/           # API tests
â”‚   â””â”€â”€ requirements.txt
â””â”€â”€ README.md
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

### 4. Start the development server

```bash
python -m uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`. Interactive API documentation is
available at `http://127.0.0.1:8000/docs`.

## Running the Tests

From the `backend` directory with the virtual environment active:

```bash
python -m pytest
```

The current tests cover the health route, card creation and retrieval, partial
updates, and rejection of negative prices.

## Roadmap

- Expand tests for filtering, deletion, and error responses
- Add full pagination for larger collections
- Integrate external PokÃ©mon card data and search
- Build the collection dashboard and frontend
- Add user accounts and authentication
- Move from local SQLite storage to PostgreSQL for deployment