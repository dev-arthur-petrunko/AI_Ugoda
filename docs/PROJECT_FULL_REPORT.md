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
    alembic/versions/     # 0001, 0002, 0003, 0004, 0005
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
  - `0004_unique_constraints` (unique constraints + dedup before constraint)
  - `0005_ukrainian_fts` (switch FTS config to Ukrainian Hunspell)
- IDs unified to `String(36)`.
- Extensions enabled: `pg_trgm`, `vector`.
- `legal_provisions` has:
  - `embedding vector(1536)` with HNSW index (cosine).
  - `search_vector tsvector` generated column with GIN index (`ukrainian` config via `to_tsvector('ukrainian', ...)`).

## 4. Auth & Rate Limiting
- `AUTH_DISABLED` flag (default `false` in dev; auth required when `AUTH_DISABLED=false` or `APP_ENV=production`).
- `SECRET_KEY` startup check in production (raises RuntimeError if `dev-secret-change-me`).
- Rate limiting middleware: 120 req/min per IP (in-memory), Redis primary with in-memory fallback, exempts `/health`, `/`, docs.

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
- Ukrainian morphology for FTS implemented (migration 0005, hunspell-uk in Docker image) but NOT verified against live PostgreSQL (Docker unavailable in this environment).
- Embeddings are not yet generated (column exists, data not populated).
- Some pages are informational/static (assistant, changes, conflicts, contracts, legal-map, monitoring, reports, settings, workspace).
- CSS tokens partly aliased (`--cream` vs `--text`).

## 11. Changelog (recent)
- `da73f6d` fix(K1): auth AND condition, removed dead code import_service, added 401 test, AUDIT report.
- `c381fb5` feat: Hunspell Ukrainian FTS, Redis rate limiter, unique constraints/upserts, branded logo & splash.
- Earlier: PostgreSQL migration, ruff cleanup, status audit.

---
Generated automatically as project completion report.


## 12. Detailed Process (Chronological)

### Phase A — PostgreSQL migration
- Set up PostgreSQL 16 via Docker Compose.
- Switched `.env` to PostgreSQL URL.
- Created Alembic migrations `0001`, `0002`.
- Migrated SQLite data to PostgreSQL in Python (psycopg2 + sqlite3), with boolean coercion.
- Verified `/api/v1/stats`, `/documents`, pytest (7/7), frontend (200).

### Phase B — Cleanup & lint
- Applied ruff cleanup to 0 errors.
- Added `apps/api/pyproject.toml` ruff config (documented ignores B008, F821).
- Fixed `alembic.ini` script_location for Docker portability.
- Rebuilt/restarted stack; health OK.
- Pushed to origin/main.

### Phase C — Auth & rate limiting (Stage 4)
- Added `AUTH_DISABLED`, `RATE_LIMIT_PER_MINUTE`.
- Updated `get_current_user` for auth flags.
- Added rate limiting middleware (per IP, in-memory).
- Added startup checks for production SECRET_KEY/AUTH_DISABLED.

### Phase D — pgvector & FTS (Stage 5)
- Switched Postgres image to `pgvector/pgvector:pg16`.
- Added migration `0003_pgvector_fts`:
  - extensions `vector`, `pg_trgm`
  - `embedding vector(1536)` + HNSW index
  - `search_vector tsvector` generated column + GIN index
- Updated `LegalProvision` model with dialect-aware types (SQLite tests preserved).

### Phase E — Error fixing & verification
- Fixed Docker healthchecks (removed curl dependency; use Python/Node).
- Unified duplicate CSS design tokens into a single `:root`.
- Verified ruff 0, pytest 7/7, frontend build, Docker health.

### Phase F — Documentation
- Added `docs/PROJECT_FULL_REPORT.md` with architecture, DB, auth, search, frontend, Docker, testing, env, limitations, changelog.

## 13. Completed (Done)
- ruff 0 errors.
- pytest 11 passed / 2 skipped (FTS needs PostgreSQL).
- Frontend build successful.
- Auth flags + rate limiting (Redis + in-memory fallback).
- pgvector + FTS schema (migrations 0003–0005).
- Branded logo (Терези рівноваги) + Splash screen.
- Unique constraints + idempotent upserts (nreg, revision, provision).
- Documentation: CLEANUP_REPORT.md, AUDIT_2026-10-26.md, PROJECT_DOCUMENTATION.md.

## 14. Not Completed / Blocked
- Ukrainian FTS not verified against live PostgreSQL (Docker Desktop unavailable).
- Embedding generation (column exists, data not populated).
- Full wiring of 9 informational pages to API.
- Deeper CSS token alias cleanup (`--cream` vs `--text`).
- Production auth (JWT/OAuth) not fully implemented; currently simple token/flag.
- CVE in dependencies (pip-audit 98, npm audit 2) — requires dependency updates.
- Docker daemon not running → cannot validate FTS/migrations/build image.

## 15. Errors Fixed
- Auth: `AUTH_DISABLED OR APP_ENV=development` → `AND`; `AUTH_DISABLED=False` default; anonymous user without admin rights.
- Removed dead code in `import_service.py:upsert_force_level`.
- Ruff errors (B008/F821 documented) → 0 errors.
- Docker healthchecks fixed (Python/Node instead of curl).
- Model compatibility with SQLite tests (Vector/TSVECTOR dialect-aware).
