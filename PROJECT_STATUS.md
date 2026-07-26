# Cardfolio Project Status

Last updated: 2026-07-25  
Branch: `main`  
Checkpoint commit: `fe050e6`

## Current Checkpoint

- FastAPI backend with separated card routes
- Card create, list, partial update, and delete endpoints
- Partial name filtering and bounded result limits
- Pydantic validation with SQLAlchemy and SQLite persistence
- Eleven test functions covering twelve cases with an in-memory test database
- Null-name updates rejected by the API
- Generated SQLite files excluded from Git

## Verification

- Recent commit history records the current test suite as passing.
- The suite was not rerun during this inspection because the local environment
  does not currently contain the documented test tools.

## Active Issues

- Application imports can create the development database during tests.
- Database configuration depends on the process working directory.
- The database permits a null card name even though the API rejects it.
- Dependency declarations and local test setup need consolidation.
- Card-list ordering is not deterministic.
- README coverage and roadmap details are stale.

## Next Milestone

Harden database configuration and test isolation, then reverify the complete
test suite.

See `ROADMAP.md` for the long-term development plan.

Update this file only when completed work, test status, active issues, or the
next milestone changes.
