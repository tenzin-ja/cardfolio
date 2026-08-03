# Cardfolio Project Status

Last updated: 2026-08-03
Last environment: Windows desktop
Branch: `main`
Roadmap position: The Portfolio Data Model is underway. The initial
`CatalogCard` model and migration are complete; `CardVariant` is next.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete endpoints for the temporary `Card` resource
- Partial, case-insensitive name filtering and bounded result limits
- Fourteen test functions covering fifteen cases with an isolated in-memory
  database
- Alembic `1.18.5` is the only application-schema manager
- Three migrations: initial `cards`, required card names, and `catalog_cards`
- Development database is at revision `64e710e11ea7 (head)`
- Existing `Card` table and data were preserved while `catalog_cards` was added
- Local SQLite files are excluded from Git

## Completed This Session

- Repaired a merge regression that restored import-time table creation
- Kept schema creation under Alembic by removing
  `Base.metadata.create_all()` from the FastAPI application
- Designed and added the initial `CatalogCard` SQLAlchemy model
- Added provider-scoped external identity with a composite unique constraint
- Added catalog identity, set information, image metadata, and nullable
  reference-price fields
- Defined the initial reference price as a raw Near Mint estimate with explicit
  variant, source, observation time, and currency metadata
- Generated, reviewed, and applied revision `64e710e11ea7`
- Added a database-level test proving duplicate provider identities are rejected

## Verification

- `python -m pytest`: 15 passed
- `alembic current`: `64e710e11ea7 (head)`
- SQLAlchemy metadata contains both `cards` and `catalog_cards`
- Alembic detected only the expected new table and name index before migration
- The catalog migration does not alter or delete the existing `cards` table

## V1 Decisions

- Support Pokemon cards only in V1
- Support raw/ungraded cards; graded cards are postponed
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
- `CardVariant`, `CollectionItem`, `PriceSnapshot`, and `User` are not implemented
- Reference pricing currently lives on `CatalogCard`; lasting variant-specific
  pricing and price history still need to be modeled
- `CatalogCard` does not yet have Pydantic schemas, routes, or an import service
- Card-list ordering is not deterministic
- Offset/cursor pagination is not implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not reflect all current V1 decisions

## Exact Next Action

Agree on the responsibility and minimal fields for `CardVariant`, including how
it identifies finishes such as normal, holofoil, and reverse holofoil. Then add
the model, Alembic registration, migration, and one focused test as separate,
verified steps.

Preserve the existing `Card` table and the new `CatalogCard` fields until there
is an explicit data-migration plan. Do not begin `CollectionItem` until its
lasting relationship to `CardVariant` is clear.

On a new computer, pull the repository, create or activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
