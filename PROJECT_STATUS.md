# Cardfolio Project Status

Last updated: 2026-07-29
Last environment: Work Windows desktop
Branch: `main`
Last completed code commit before this handoff: `b1a2f03`
Roadmap position: Backend Foundation is complete enough to begin the Portfolio
Data Model; stable collection ordering and pagination remain future retrieval
work.

## Current Checkpoint

- FastAPI backend with create, list, exact-ID retrieval, partial-update, and
  delete card endpoints
- Partial, case-insensitive name filtering and bounded result limits
- Thirteen test functions covering fourteen cases with an isolated in-memory
  database
- Local SQLite files excluded from Git
- Predictable SQLite path with a `DATABASE_URL` override
- Alembic `1.18.5` configured as the only application-schema manager
- Two migrations: the initial `cards` table and required card names
- Existing development database is tracked locally at Alembic head
- Cross-platform Git line endings configured for Windows and macOS

## Completed This Session

- Verified that the existing `cards.db` schema matched the initial migration
- Stamped the existing database at revision `1b5368fe8921`
- Removed import-time `Base.metadata.create_all()` from the FastAPI application
- Configured Alembic batch mode for SQLite column changes
- Changed `Card.name` to `nullable=False`
- Generated and applied revision `d5ee3bb4be7f` to require card names
- Added `GET /cards/{card_id}` for backend retrieval of one exact card
- Added successful and missing-card tests for exact-ID retrieval
- Clarified that users will search by meaningful card information; internal IDs
  are used by the frontend after a user selects a result

## Verification

- `python -m pytest`: 14 passed
- `alembic current`: `d5ee3bb4be7f (head)`
- SQLite reports `cards.name` with `notnull = 1`
- All 6 existing development cards were preserved
- Existing null-name count: 0

## V1 Decisions

- Support Pokemon cards only in V1
- Support raw/ungraded cards; graded cards are postponed
- Store condition but do not invent automatic condition-based price adjustments
- Use Pokemon TCG API catalog data and TCGplayer-derived reference prices
- Show eBay active listings later as comparisons, not confirmed market value
- Import catalog cards on demand rather than mirroring the entire external catalog
- Include registration and private collections before release, while postponing
  authentication implementation until the core collection workflow is stable
- Do not provide user-facing search by internal database ID
- Keep AI-assisted condition suggestions and soccer cards as possible later work

## Active Issues

- The current `Card` table still combines catalog identity and collection data
- `CatalogCard`, `CardVariant`, `CollectionItem`, `PriceSnapshot`, and `User`
  models are not yet implemented
- Card-list ordering is not deterministic
- Offset/cursor pagination is not yet implemented
- Root and backend dependency declarations need consolidation
- README and roadmap do not yet reflect all current V1 decisions
- Exact-ID routes will need to target the lasting catalog and collection models
  after the data-model split

## Exact Next Action

Begin the Portfolio Data Model by agreeing on the responsibilities and initial
fields for `CatalogCard` and `CollectionItem`. Preserve the existing `Card` table
until there is an explicit data-migration plan. Add the lasting models and their
migration in small, separately verified steps.

After the model split, apply deterministic ordering and pagination to the lasting
collection endpoint rather than expanding the temporary combined `Card` resource.

On a new computer, pull the repository, create/activate the backend virtual
environment, install backend requirements, and run `alembic upgrade head`.
