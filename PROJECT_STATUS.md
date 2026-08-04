# Cardfolio Project Status

Last updated: 2026-08-04
Last environment: Windows desktop
Branch: `main`
Roadmap position: The Portfolio Data Model is underway. The initial
`CatalogCard` and `CardVariant` models and migrations are complete;
`CollectionItem` is next.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Fifteen test functions covering sixteen cases with an isolated in-memory
  database
- Alembic `1.18.5` is the only application-schema manager
- Four migrations: initial `cards`, required card names, `catalog_cards`, and
  `card_variants`
- Development database is at revision `0eac98a8accb (head)`
- `CatalogCard` has a one-to-many relationship with `CardVariant`
- Existing `Card` and `CatalogCard` data were preserved while `card_variants`
  was added
- Local SQLite files are excluded from Git

## Completed This Session

- Clarified that one `CatalogCard` represents one distinct card printing, not a
  search term or every card sharing the same name
- Designed and added the initial `CardVariant` SQLAlchemy model
- Added the `catalog_card_id` foreign key and lookup index
- Added a composite unique constraint on `catalog_card_id` and `variant_key`
- Added bidirectional `CatalogCard.variants` and `CardVariant.catalog_card`
  relationships
- Registered `CardVariant` with Alembic
- Generated, reviewed, and applied revision `0eac98a8accb`
- Added a database-level test proving one catalog card cannot store the same
  variant key twice

## Verification

- `python -m pytest`: 16 passed
- `alembic current`: `0eac98a8accb (head)`
- `alembic check`: no new upgrade operations detected
- SQLAlchemy metadata contains the `card_variants` table, foreign key, composite
  unique constraint, and catalog-card index
- Bidirectional relationship mapper check passed
- The variant migration does not alter or delete existing tables or data

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
- `CollectionItem`, `PriceSnapshot`, and `User` are not implemented
- Reference pricing currently lives on `CatalogCard`; lasting variant-specific
  pricing and price history still need to be modeled
- `CatalogCard` and `CardVariant` do not yet have Pydantic schemas, routes, or an
  import service
- SQLite foreign-key enforcement is not explicitly enabled and tested yet
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Verify and explicitly enable SQLite foreign-key enforcement for development and
test connections. Then agree on the responsibility and minimal fields for
`CollectionItem`, including its `CardVariant` relationship, condition, quantity,
and purchase information.

Add `CollectionItem`, its Alembic migration, and one focused database test as
separate, verified steps. Preserve the temporary `Card` table and current
reference-price fields until there is an explicit data-migration plan.

On a new computer, pull the repository, create or activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
