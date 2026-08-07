# Cardfolio Project Status

Last updated: 2026-08-07
Last environment: Windows desktop
Branch: `main`
Roadmap position: The Portfolio Data Model is underway. The initial
`CatalogCard`, `CardVariant`, and `CollectionItem` models and migrations are
complete, and the first real `CollectionItem` API slice is underway. Its
Pydantic schemas and POST router are written; the router still needs to be
connected to the FastAPI application and tested through HTTP.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Eighteen test functions covering nineteen cases with an isolated in-memory
  database
- Alembic `1.18.5` is the only application-schema manager
- Five migrations: initial `cards`, required card names, `catalog_cards`,
  `card_variants`, and `collection_items`
- Development database is at revision `b947a39991a6 (head)`
- `CatalogCard` has many `CardVariant` rows, and each `CardVariant` can have many
  owned `CollectionItem` rows
- SQLite foreign-key enforcement is enabled for development and test
  connections
- `CollectionItemCreate` and `CollectionItemResponse` define the initial API
  input and output contract
- A `POST /collection-items` route is implemented but is not yet included in
  `main.py`
- Existing `Card`, `CatalogCard`, and `CardVariant` data were preserved while
  `collection_items` was added
- Local SQLite files are excluded from Git

## Completed This Session

- Added a database test proving an unsupported collection-item condition is
  rejected
- Added `CollectionItemCreate` with validation for condition, quantity,
  per-card purchase price, currency, purchase date, and notes
- Used `Decimal` for API purchase prices and exposed the six canonical condition
  values through the Pydantic schema
- Added `CollectionItemResponse` with ORM attribute serialization
- Added the initial `POST /collection-items` route
- Added a friendly 404 check when the requested `CardVariant` does not exist
- Added model conversion, commit, refresh, and 201 response behavior to the
  create route

## Verification

- `python -m pytest`: 19 passed before the new router was added
- `alembic current`: `b947a39991a6 (head)`
- `alembic check`: no new upgrade operations detected
- Development and test connections report `PRAGMA foreign_keys = 1`
- The `CardVariant`/`CollectionItem` bidirectional mapper check passed
- The collection-item migration contains all eight columns, three check
  constraints, its foreign key, primary key, and lookup index
- The collection-item migration does not alter or delete existing tables or
  data
- Pydantic schema check confirmed the default quantity and currency, zero-dollar
  purchases, and the canonical condition choices
- The new router imports successfully and registers `/collection-items`; it is
  not yet covered by an HTTP test

## V1 Decisions

- Support Pokemon cards only in V1
- Support raw/ungraded cards; graded cards are postponed
- Treat each distinct provider card printing as a separate `CatalogCard`, even
  when multiple cards share the same name
- Use `CardVariant` for a printing's finish or version, not an owned copy's
  condition
- Import catalog cards on demand from the Pokemon TCG API
- Use TCGplayer-derived prices as reference values
- Treat a catalog reference price as a shared raw Near Mint baseline
- Store an owned card's condition without overwriting the shared catalog price
- Do not invent automatic condition-based price adjustments
- Show eBay active listings later as comparisons, not confirmed market value
- Include registration and private collections before release, while postponing
  authentication until the core collection workflow is stable
- Do not provide user-facing search by internal database ID

## Active Issues

- The temporary `Card` table still combines catalog identity and collection data
- `PriceSnapshot` and `User` are not implemented
- Reference pricing currently lives on `CatalogCard`; lasting variant-specific
  pricing and price history still need to be modeled
- `CatalogCard` and `CardVariant` do not yet have Pydantic schemas, routes, or an
  import service
- The `CollectionItem` router is not connected to `main.py` and does not yet
  provide list, detail, update, or delete operations
- Nonpositive quantity, negative purchase price, and missing-variant rejection
  cases are not yet covered by focused `CollectionItem` tests
- The condition dropdown will be implemented with the frontend; the database
  currently enforces its canonical values
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Import the collection-items router in `main.py`, include it in the FastAPI
application, and add one HTTP test proving a valid request returns 201 and a
saved `CollectionItem`. Then add `GET /collection-items` so the frontend will
have both create and list operations.

Keep tests attached to each backend feature. Batch the remaining database
constraint cases instead of treating each one as a separate development
session.

Preserve the temporary `Card` table and current reference-price fields until
there is an explicit data-migration plan.

On a new computer, pull the repository, create or activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
