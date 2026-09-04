# Cardfolio Project Status

Last updated: 2026-09-04
Last environment: Windows desktop
Branch: `main`
Roadmap position: The External Card Catalog milestone is underway. The portfolio
data model now includes catalog cards, immutable variants, owned collection
items, current variant pricing, and historical price snapshots. Catalog-search
schemas, the Pokemon TCG response mapper, provider HTTP search, and Git-ignored
local API-key configuration, provider timeout/error handling, and the catalog
search route are in place. Development and database tests now use PostgreSQL;
catalog import persistence remains.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Thirty-eight passing test cases; database tests use the dedicated local
  PostgreSQL `cardfolio_test` database
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
- PostgreSQL enforces foreign keys in both development and test databases
- `CollectionItemCreate`, `CollectionItemUpdate`, and `CollectionItemResponse`
  define the current API contract
- Collection-item create, list, partial-update, and delete operations are
  connected to FastAPI; the selected variant is immutable after creation
- Catalog-search schemas and Pokemon TCG mapping functions normalize external
  identity, image, pagination, variant, and market-price data
- `search_pokemon_cards` performs authenticated provider searches with
  pagination and supports an injected HTTP client for isolated tests
- Local configuration loads the provider key from a Git-ignored `backend/.env`
  while allowing deployed environment variables to take priority
- The variant-pricing migration adds and removes columns directly
- The pricing migration supplies a database-level `USD` default so existing
  variants receive the new required currency value
- `.env` credentials and local `*.db` files are excluded from Git

## PostgreSQL Checkpoint

- PostgreSQL 18.6 runs locally; the app connects to `cardfolio` as the
  non-superuser `cardfolio_app`
- `DATABASE_URL` is required, with no database fallback; `psycopg[binary]` is
  declared in the backend requirements
- All seven existing migrations have been applied to the development database
- Tests require `TEST_DATABASE_URL` targeting local `cardfolio_test`; URL and
  connected-database checks run before test table cleanup
- Each database test creates and drops model tables; run the suite sequentially
- Alembic configuration escapes percent signs in URL-encoded passwords and no
  longer selects database-specific batch mode
- Existing data from the previous database was not copied into PostgreSQL

## Earlier Completed Work

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
- Started the Pokemon TCG HTTP integration test-first with a mocked successful
  search request; no real provider call or API quota is used by the test
- Defined the expected provider endpoint, API-key header, search parameters,
  pagination parameters, and mapped Cardfolio response in the new test
- Implemented `search_pokemon_cards` and satisfied the mocked HTTP request
  contract without making the automated suite depend on the network
- Added local `.env` loading, a safe committed `.env.example`, a clear
  configuration error, and focused environment-configuration tests
- Completed a controlled live provider smoke test that returned normalized card
  identity, image, variant, and TCGplayer market-price data

## Verification

- Latest user-reported `python -m pytest -q`: 38 passed in 5.69 seconds with
  one Starlette/httpx deprecation warning, using PostgreSQL for database tests
- Application connection check returned `('cardfolio', 'cardfolio_app')`
- The current fixture creates tables from model metadata; passing tests do not
  independently verify the Alembic migration chain
- The mocked provider test verified the endpoint, API-key header, name query,
  pagination parameters, injected client, and normalized response
- Configuration tests verified environment-key retrieval and a clear error when
  the required key is absent
- A live one-result Charizard search returned `gym2-2` (Blaine's Charizard), its
  image, and separate first-edition and unlimited holofoil market prices
- `alembic current`: `959d95fa90be (head)`
- Earlier migration checks verified currency backfilling and preservation of
  linked data on the previous database; those checks have not been repeated
  against PostgreSQL
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
- Use PostgreSQL for development and database tests, with separate databases
- Support raw/ungraded cards; graded cards are postponed
- Treat each distinct provider card printing as a separate `CatalogCard`, even
  when multiple cards share the same name
- Use `CardVariant` for a printing's finish or version, not an owned copy's
  condition
- Keep an owned collection item's selected variant immutable after creation
- Import catalog cards on demand from the Pokemon TCG API
- Use TCGplayer-derived prices as reference values
- Keep the Pokemon TCG API as the V1 catalog and baseline raw-price provider;
  defer richer condition, graded, and historical providers until they are needed
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
- Catalog search has timeout/error handling and tests; the import route is not
  implemented, and selected results are not yet persisted as `CatalogCard` and
  `CardVariant` rows
- Provider refreshes do not yet update current variant prices or create
  `PriceSnapshot` history rows
- Any separately preserved database that already applied the pre-fix
  `7f64a6890b0e` revision must be rebuilt or reconciled because Alembic does not
  rerun an edited migration
- Define the API's timestamp representation before exposing price history;
  PostgreSQL stores observation timestamps with time zone
- A single-item collection GET operation is not yet implemented
- Nonpositive quantity, negative purchase price, and missing-variant rejection
  cases are not yet covered by focused `CollectionItem` tests
- Rejection of attempts to change a collection item's immutable variant is not
  yet covered by a focused API test
- The condition dropdown will be implemented with the frontend; the database
  currently enforces its canonical values
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Separate root and backend requirements files still need consolidation;
  `python-dotenv` and Psycopg are declared in the backend requirements
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Resume catalog import persistence. `catalog_import.py` currently contains
imports and the price-source constant; implement saving a normalized provider
card and its variants, then verify initial import and re-import behavior with
PostgreSQL tests before adding the import route.

When catalog import and refresh are added, update each `CardVariant`'s current
price fields and append a `PriceSnapshot` without changing owned-card condition
data.

Keep tests attached to each backend feature. Batch the remaining database
constraint cases instead of treating each one as a separate development
session.

Preserve the temporary `Card` table and current reference-price fields until
there is an explicit data-migration plan.

On a new computer, set up the repository and backend virtual environment,
install backend requirements, and create the PostgreSQL login and separate
development/test databases. Configure the ignored `.env` from `.env.example`,
run `alembic upgrade head` for development, and run the tests. See README for
the setup commands.
