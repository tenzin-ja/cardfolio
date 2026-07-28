# Cardfolio Project Status

Last updated: 2026-07-28
Last environment: Work Windows desktop
Branch: `main`
Last completed code commit: `27e9fec`
Roadmap milestone: Backend Foundation, with migration infrastructure begun for
the Portfolio Data Model milestone

## Current Checkpoint

- FastAPI backend with create, list, partial-update, and delete card endpoints
- Partial, case-insensitive name filtering and bounded result limits
- Eleven test functions covering twelve cases with an isolated in-memory
  database
- Null-name updates rejected before they can erase a required card name
- Local SQLite files excluded from Git
- Predictable SQLite path based on the backend directory
- `DATABASE_URL` override available for tests and future deployment
- Alembic `1.18.5` installed and recorded in backend dependencies
- Alembic configured to use Cardfolio's database URL and SQLAlchemy metadata
- Initial revision `1b5368fe8921` creates the current `cards` table and indexes
- Cross-platform Git line endings configured for Windows and macOS

## Completed This Session

- Committed and pushed database configuration and test-isolation changes in
  `b3e0c98`
- Added and configured Alembic in commit `27e9fec`
- Generated the initial `cards` table migration
- Documented how `ROADMAP.md` and `PROJECT_STATUS.md` guide future sessions
- Confirmed the V1 catalog approach: search the external Pokémon TCG API and
  import only cards selected by users

## Verification

- `python -m pytest`: 12 passed
- Initial Alembic revision applied successfully to disposable
  `alembic_test.db`
- `alembic current` reported `1b5368fe8921 (head)`
- `alembic downgrade base` successfully reversed the disposable database
- Disposable migration-test database was removed afterward

## V1 Decisions

- Support Pokémon cards only in V1
- Support raw/ungraded cards; graded cards are postponed
- Store condition but do not invent automatic condition-based price adjustments
- Use Pokémon TCG API catalog data and TCGplayer-derived reference prices
- Show eBay active listings later as comparisons, not confirmed market value
- Import catalog cards on demand rather than mirroring the entire external catalog
- Include registration and private collections before release, while postponing
  authentication implementation until the core collection workflow is stable
- Keep AI-assisted condition suggestions and soccer cards as possible later work

## Active Issues

- The existing development `cards.db` has not been stamped with the initial
  Alembic revision
- `Base.metadata.create_all()` still runs when the FastAPI application is
  imported
- The SQLAlchemy model permits a null card name even though the API rejects it
- Root and backend dependency declarations still need consolidation
- Card-list ordering is not deterministic
- The README and roadmap do not yet reflect all current V1 decisions
- Catalog, variant, collection-item, price-snapshot, and user models are not yet
  implemented

## Exact Next Action

On the Work Windows desktop, verify that the existing development `cards.db`
matches revision `1b5368fe8921`, then stamp that local database at the revision
without rerunning the table-creation migration. After the database is under
Alembic control, remove import-time `Base.metadata.create_all()` and verify the
test suite again.

On a new computer with no existing database, run `alembic upgrade head` instead
of stamping so Alembic creates the schema.

Consult `ROADMAP.md` before selecting work beyond this exact action. Update this
file at the end of the next working session.
