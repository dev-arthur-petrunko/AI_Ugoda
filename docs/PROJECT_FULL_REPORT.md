# AI Ugoda — Full Project Report

## 1. Overview
AI Ugoda is a Ukrainian legal intelligence platform. It provides:
- Search and browsing of legal acts/documents.
- Revision history and provisions.
- Statistics and sync status.
- Conflict/collision explanations (UI).
- Admin panel for triggering sync.

The project consists of:
- `apps/api` — FastAPI backend (Python 3.12/3.14 compatible).
- `apps/web` — Next.js 14 frontend.
- PostgreSQL 16 + pgvector, Redis.
- Docker Compose orchestration.

## 2. Architecture
```
apps/
  api/
    app/
      api/v1/endpoints/   # documents, stats, sync, health
      core/               # config, database
      models/             # SQLAlchemy ORM
      services/           # search, import, connector, parser
      middleware/         # rate limiting
    alembic/versions/     # 0001, 0002, 0003
  web/
    src/app/uk/           # pages
    src/lib/api.ts        # API client
docker-compose.yml
```

## 3. Database & Migrations
- Migrated from SQLite to PostgreSQL.
- Alembic migrations:
  - `0001_initial_schema`
  - `0002_extend_schema`
  - `0003_pgvector_fts` (pgvector + FTS)
- IDs unified to `String(36)`.
- Extensions enabled: `pg_trgm`, `vector`.
- `legal_provisions` has:
  - `embedding vector(1536)` with HNSW index (cosine).
  - `search_vector tsvector` generated column with GIN index (`simple` config).

## 4. Auth & Rate Limiting
- `AUTH_DISABLED` flag (default `true` in dev).
- `SECRET_KEY` startup check in production.
- Rate limiting middleware: 120 req/min per IP (in-memory), exempts `/health`, `/`, docs.

## 5. Search
- `SearchService` supports filtering by type/status/authority/dates/legal force level.
- Full-text via LIKE over title/normalized text/provision text.
- Suggestions and search by provision (article number).

## 6. Frontend
- Pages: overview, legislation search/detail, admin, plus explanatory pages.
- API client in `src/lib/api.ts`.
- Design tokens unified in `globals.css`.

## 7. Docker
- Services: postgres (pgvector/pgvector:pg16), redis, api, web, worker.
- Healthchecks use Python (API) and Node (Web) — no curl dependency.
- All services healthy.

## 8. Testing & Quality
- Backend: `pytest` → 7/7 passed.
- Lint: `ruff check apps/api` → 0 errors.
- Frontend: `npm run build` → successful (16 routes).
- Docker health: all healthy.

## 9. Environment Variables
Key variables (see `.env` / `.env.example`):
- `DATABASE_URL`
- `APP_ENV`
- `SECRET_KEY`
- `AUTH_DISABLED`
- `RATE_LIMIT_PER_MINUTE`
- `CORS_ORIGINS`
- `NEXT_PUBLIC_API_URL`

## 10. Known Limitations / Next Steps
- Ukrainian morphology for FTS requires Hunspell dictionaries.
- Embeddings are not yet generated (column exists).
- Some pages are informational/static (assistant, changes, conflicts, contracts, legal-map, monitoring, reports, settings, workspace).
- CSS tokens partly aliased (`--cream` vs `--text`).

## 11. Changelog (recent)
- `9c9f6e4` feat: auth flags, rate limiting, pgvector+FTS migration.
- `730e529` fix: Docker healthchecks, unify CSS tokens.
- Earlier: PostgreSQL migration, ruff cleanup, status audit.

---
Generated automatically as project completion report.
