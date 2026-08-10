# Cardfolio Project Status

Last updated: 2026-08-10
Last environment: Windows desktop
Branch: `main`
Roadmap position: The Portfolio Data Model is underway. The initial
`CatalogCard`, `CardVariant`, and `CollectionItem` models and migrations are
complete. The real `CollectionItem` API now supports tested create and list
operations, and its partial-update schema is ready for the PATCH route.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Twenty test functions covering twenty-one cases with an isolated in-memory
  database
- Alembic `1.18.5` is the only application-schema manager
- Five migrations: initial `cards`, required card names, `catalog_cards`,
  `card_variants`, and `collection_items`
- Development database is at revision `b947a39991a6 (head)`
- `CatalogCard` has many `CardVariant` rows, and each `CardVariant` can have many
  owned `CollectionItem` rows
- SQLite foreign-key enforcement is enabled for development and test
  connections
- `CollectionItemCreate`, `CollectionItemUpdate`, and `CollectionItemResponse`
  define the current API contract
- `POST /collection-items` and `GET /collection-items` are connected to the
  FastAPI application
- Existing `Card`, `CatalogCard`, and `CardVariant` data were preserved while
  `collection_items` was added
- Local SQLite files are excluded from Git

## Completed This Session

- Connected the collection-items router to `main.py`
- Added an HTTP integration test proving a valid collection item can be created
  with a 201 response and database defaults
- Added `GET /collection-items` with a bounded limit and deterministic ID order
- Added an HTTP integration test covering collection listing, limiting, and
  ordering
- Added `CollectionItemUpdate` for partial updates
- Distinguished omitted PATCH fields from explicit null values, allowing
  optional purchase data to be cleared while protecting required columns

## Verification

- `python -m pytest`: 21 passed
- `alembic current`: `b947a39991a6 (head)`
- `alembic check`: no new upgrade operations detected
- Development and test connections report `PRAGMA foreign_keys = 1`
- The `CardVariant`/`CollectionItem` bidirectional mapper check passed
- The collection-item migration contains all eight columns, three check
  constraints, its foreign key, primary key, and lookup index
- The collection-item migration does not alter or delete existing tables or
  data
- FastAPI's generated API schema exposes GET and POST on `/collection-items`
- Pydantic update-schema checks confirmed omitted fields remain untouched,
  optional purchase prices can be cleared, and required fields reject null

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
- The `CollectionItem` router does not yet provide detail, update, or delete
  operations; its update schema is ready
- Nonpositive quantity, negative purchase price, and missing-variant rejection
  cases are not yet covered by focused `CollectionItem` tests
- The condition dropdown will be implemented with the frontend; the database
  currently enforces its canonical values
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Import `CollectionItemUpdate` into the collection-items router and implement
`PATCH /collection-items/{item_id}`. It should return 404 for a missing item,
validate a replacement variant when supplied, apply only fields present in the
request, and return the refreshed item.

Add one focused HTTP test for a successful partial update, then proceed to the
delete operation.

Keep tests attached to each backend feature. Batch the remaining database
constraint cases instead of treating each one as a separate development
session.

Preserve the temporary `Card` table and current reference-price fields until
there is an explicit data-migration plan.

On a new computer, pull the repository, create or activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
