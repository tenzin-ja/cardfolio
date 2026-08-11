# Cardfolio Project Status

Last updated: 2026-08-11
Last environment: Windows desktop
Branch: `main`
Roadmap position: The Portfolio Data Model is underway. The initial
`CatalogCard`, `CardVariant`, and `CollectionItem` models and migrations are
complete. The real `CollectionItem` API now supports tested create, list,
update, and delete operations. External catalog integration has begun with
normalized search schemas and a pure Pokemon TCG response-mapping service.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Twenty-two test functions covering twenty-three cases with an isolated
  in-memory
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
- `POST`, `GET`, `PATCH`, and `DELETE` collection-item operations are connected
  to the FastAPI application
- Catalog-search schemas and Pokemon TCG mapping functions normalize external
  identity, image, pagination, variant, and market-price data
- Existing `Card`, `CatalogCard`, and `CardVariant` data were preserved while
  `collection_items` was added
- Local SQLite files are excluded from Git

## Completed This Session

- Added `PATCH /collection-items/{item_id}` with partial-field application,
  missing-item handling, and replacement-variant validation
- Added an HTTP integration test proving PATCH changes only supplied fields
- Added `DELETE /collection-items/{item_id}` with an empty 204 response
- Added an HTTP integration test proving deletion removes the owned item while
  preserving its shared variant
- Added normalized catalog card, variant-price, and paginated search schemas
- Added a dedicated Pokemon TCG service module with pure functions for card,
  price, variant-key, and search-response mapping

## Verification

- `python -m pytest`: 23 passed
- `alembic current`: `b947a39991a6 (head)`
- `alembic check`: no new upgrade operations detected
- Development and test connections report `PRAGMA foreign_keys = 1`
- The `CardVariant`/`CollectionItem` bidirectional mapper check passed
- The collection-item migration contains all eight columns, three check
  constraints, its foreign key, primary key, and lookup index
- The collection-item migration does not alter or delete existing tables or
  data
- FastAPI's generated API schema exposes create, list, update, and delete
  collection-item operations
- Pydantic update-schema checks confirmed omitted fields remain untouched,
  optional purchase prices can be cleared, and required fields reject null
- Representative mapping check converted `base1-4`, nested set and image data,
  pagination, Decimal prices, and `reverseHolofoil` to `reverse_holofoil`

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
- The Pokemon TCG service does not yet make HTTP requests, read an API key, or
  handle timeouts, rate limits, and provider errors
- Catalog search and import routes are not implemented, and selected results are
  not yet persisted as `CatalogCard` and `CardVariant` rows
- A single-item collection GET operation is not yet implemented
- The pure Pokemon response mapper has a manual verification check but not yet
  an automated unit test
- Nonpositive quantity, negative purchase price, and missing-variant rejection
  cases are not yet covered by focused `CollectionItem` tests
- The condition dropdown will be implemented with the frontend; the database
  currently enforces its canonical values
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Add one focused unit test for the pure Pokemon response mapper, then implement
the service's real `httpx` search request with an environment-supplied API key,
an explicit timeout, and provider-error translation. Follow it with
`GET /catalog/search` so the frontend can search without contacting the provider
directly.

Keep tests attached to each backend feature. Batch the remaining database
constraint cases instead of treating each one as a separate development
session.

Preserve the temporary `Card` table and current reference-price fields until
there is an explicit data-migration plan.

On a new computer, pull the repository, create or activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
