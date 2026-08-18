# Cardfolio Project Status

Last updated: 2026-08-17
Last environment: macOS desktop
Branch: `main`
Roadmap position: The External Card Catalog milestone is underway. The portfolio
data model now includes catalog cards, immutable variants, owned collection
items, current variant pricing, and historical price snapshots. Catalog-search
schemas and the pure Pokemon TCG response mapper are in place; provider HTTP
search and import persistence remain.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Twenty-six test functions covering twenty-seven cases; database tests use an
  isolated in-memory database
- Alembic `1.18.5` is the only application-schema manager
- Seven migrations: initial `cards`, required card names, `catalog_cards`,
  `card_variants`, `collection_items`, variant pricing, and `price_snapshots`
- Development database is at revision `959d95fa90be (head)`
- Application startup registers `Card`, `CatalogCard`, `CardVariant`,
  `CollectionItem`, and `PriceSnapshot` with SQLAlchemy
- `CatalogCard` has many `CardVariant` rows, and each `CardVariant` can have many
  owned `CollectionItem` and historical `PriceSnapshot` rows
- `CardVariant` stores the latest market price, source, update time, and currency
- `PriceSnapshot` stores exact historical prices with a nonnegative-price
  constraint, cascading variant foreign key, and chart-query index
- SQLite foreign-key enforcement is enabled for development and test
  connections
- `CollectionItemCreate`, `CollectionItemUpdate`, and `CollectionItemResponse`
  define the current API contract
- Collection-item create, list, partial-update, and delete operations are
  connected to FastAPI; the selected variant is immutable after creation
- Catalog-search schemas and Pokemon TCG mapping functions normalize external
  identity, image, pagination, variant, and market-price data
- The variant-pricing migration uses direct SQLite column additions/removals,
  avoiding a table rebuild while preserving linked collection items
- The pricing migration supplies a database-level `USD` default so existing
  variants receive the new required currency value
- Local SQLite files are excluded from Git

## Completed This Session

- Fixed SQLAlchemy model registration during normal application startup
- Made a collection item's selected `CardVariant` immutable after creation
- Added current market-price fields to `CardVariant` and a safe currency default
- Added the `PriceSnapshot` model, migration, bidirectional relationship,
  nonnegative-price constraint, cascading delete behavior, and composite index
- Added focused tests for snapshot persistence and defaults, negative-price
  rejection, and deletion with preservation of the shared `CatalogCard`
- Corrected the variant-pricing migration to add and remove columns directly
  instead of rebuilding the foreign-key-referenced `card_variants` table
- Upgraded the development database through the corrected migration to
  `959d95fa90be (head)`

## Verification

- `python -m pytest`: 27 passed with one unrelated Starlette/httpx deprecation
  warning
- `alembic current`: `959d95fa90be (head)`
- `alembic check`: no new upgrade operations detected
- A populated `b947a39991a6 -> head -> b947a39991a6 -> head` migration test
  preserved the catalog card, variant, and linked collection item
- The corrected migration backfilled `USD`, left no Alembic temporary table,
  and completed with no SQLite foreign-key violations
- Development and test connections report `PRAGMA foreign_keys = 1`
- Clean SQLAlchemy mapper configuration succeeds during normal app loading
- The `CardVariant`/`PriceSnapshot` bidirectional relationship check passed
- Snapshot checks confirmed `USD` and observation-time defaults, exact Decimal
  prices, negative-price rejection, and cascading history deletion
- Deleting a variant removes its price snapshots while preserving its shared
  `CatalogCard`
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
- Keep an owned collection item's selected variant immutable after creation
- Import catalog cards on demand from the Pokemon TCG API
- Use TCGplayer-derived prices as reference values
- Treat each variant's current market price as a shared raw Near Mint baseline
- Store historical provider observations as `PriceSnapshot` rows per variant
- Store an owned card's condition without overwriting shared variant pricing
- Do not invent automatic condition-based price adjustments
- Show eBay active listings later as comparisons, not confirmed market value
- Include registration and private collections before release, while postponing
  authentication until the core collection workflow is stable
- Do not provide user-facing search by internal database ID

## Active Issues

- The temporary `Card` table still combines catalog identity and collection data
- `User` and collection ownership are not implemented
- Legacy reference-price fields still live on `CatalogCard` alongside the new
  variant-level pricing fields and need an explicit migration plan
- The Pokemon TCG service does not yet make HTTP requests, read an API key, or
  handle timeouts, rate limits, and provider errors
- Catalog search and import routes are not implemented, and selected results are
  not yet persisted as `CatalogCard` and `CardVariant` rows
- Provider refreshes do not yet update current variant prices or create
  `PriceSnapshot` history rows
- Any separately preserved database that already applied the pre-fix
  `7f64a6890b0e` revision must be rebuilt or reconciled because Alembic does not
  rerun an edited migration
- SQLite returns persisted `PriceSnapshot.observed_at` values without timezone
  information; UTC normalization is still needed before exposing price history
- A single-item collection GET operation is not yet implemented
- Nonpositive quantity, negative purchase price, and missing-variant rejection
  cases are not yet covered by focused `CollectionItem` tests
- Rejection of attempts to change a collection item's immutable variant is not
  yet covered by a focused API test
- The condition dropdown will be implemented with the frontend; the database
  currently enforces its canonical values
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Implement the Pokemon TCG service's real `httpx` search request with an
environment-supplied API key, an explicit timeout, and provider-error
translation. Follow it with `GET /catalog/search` so the frontend can search
without contacting the provider directly.

When catalog import and refresh are added, update each `CardVariant`'s current
price fields and append a `PriceSnapshot` without changing owned-card condition
data.

Keep tests attached to each backend feature. Batch the remaining database
constraint cases instead of treating each one as a separate development
session.

Preserve the temporary `Card` table and current reference-price fields until
there is an explicit data-migration plan.

On a new computer, pull the repository, create or activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
