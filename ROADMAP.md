# Cardfolio Roadmap

Cardfolio is a trading-card collection and portfolio application. Development
is organized into small, testable milestones, with the backend established
before expanding into external data and frontend features.

## 1. Backend Foundation

Strengthen database configuration, test isolation, dependency management, and
data constraints.

Key outcomes:

- Tests never create or modify the development database.
- Database configuration is predictable and can be overridden for tests.
- Development and database tests use PostgreSQL in separate databases.
- Pydantic and SQLAlchemy enforce consistent data rules.
- Development and test dependencies have one clear setup.

## 2. Card Retrieval and Pagination

Complete the read API with individual-card retrieval and deterministic,
validated pagination.

Key outcomes:

- Retrieve one card by ID.
- Return consistent not-found responses.
- Apply stable ordering to card lists.
- Support validated pagination alongside name filtering.

## 3. Portfolio Data Model

Expand the card model from basic CRUD data into a useful portfolio record and
introduce database migrations.

Key outcomes:

- Define ownership, quantity, purchase, value, and card identity fields.
- Use appropriate database types for monetary values.
- Apply schema changes through repeatable migrations.
- Preserve existing data when the schema evolves.

## 4. External Card Catalog

Integrate an external card-data provider through a dedicated service layer.

Key outcomes:

- Search an external card catalog.
- Import selected card data into Cardfolio.
- Handle authentication, timeouts, rate limits, and provider errors.
- Test integrations with mocked provider responses.

## 5. Collection Dashboard

Build a focused frontend for managing and viewing the collection.

Key outcomes:

- Browse, search, add, edit, and delete cards.
- Display loading, empty, validation, and error states.
- Navigate paginated card results.
- Show a basic portfolio summary.

## 6. AI/MCP Integration

Add an optional Model Context Protocol (MCP) layer after Cardfolio's core API
and dashboard workflows are stable. Keep FastAPI as the canonical application
API and expose focused AI tools through a thin MCP adapter.

Key outcomes:

- Expose read-only tools for catalog search, collection listing, and portfolio
  summaries.
- Connect and test the MCP server locally with Codex.
- Reuse Cardfolio's existing service and API boundaries rather than duplicating
  business logic in the MCP layer.
- Defer collection-changing tools until user authentication, authorization,
  and explicit confirmation safeguards are available.
- Prepare the MCP integration for a remotely hosted endpoint after production
  deployment.

## Later Work

- User accounts and collection ownership
- Authentication and authorization
- Production deployment with PostgreSQL
- Automated CI checks
- Expanded portfolio analytics

## Document Roles

- `ROADMAP.md` describes the long-term direction and should change only when
  project priorities or milestone scope changes.
- `PROJECT_STATUS.md` records the current checkpoint and should remain brief.
