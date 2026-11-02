# AI Ugoda — Full Project Report

Дата оновлення: 02.11.2026

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
- JWT auth implemented in `app/api/deps.py`: decode token (jose), user lookup by email (`sub` claim), `is_superuser`/inactive checks, roles user/admin.
- `/api/v1/stats` is **public** (no JWT) so the dashboard shows real numbers without login; protected endpoints (bookmarks/monitoring/contracts) return 401 without token.
- Security headers middleware in `main.py`: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CSP.
- `SECRET_KEY` startup check in production (raises RuntimeError if `dev-secret-change-me`).
- Rate limiting middleware: 120 req/min per IP (in-memory), Redis primary with in-memory fallback, exempts `/health`, `/`, docs.

## 5. Search
- `SearchService` supports filtering by type/status/authority/dates/legal force level.
- Full-text via LIKE over title/normalized text/provision text.
- Suggestions and search by provision (article number).

## 6. Frontend
- Pages: `/uk` overview, legislation search/detail, admin, bookmarks, monitoring, contracts, plus explanatory pages (changes, conflicts, legal-map, assistant, reports, settings, workspace).
- API client in `src/lib/api.ts` (stats, documents, sync, analysis, bookmarks, monitoring, contracts).
- Design tokens unified in `globals.css` (single `:root`).
- **Interactive 3D scene** (`components/InteractiveScene.tsx`, Three.js): title «AI Ugoda · Верховна Рада», place «Київ. Площа Конституції», 7 hotspots navigate to site sections; drag to rotate, wheel to zoom, click to open section.
- **Day/night toggle** («☀ Світла» / «🌙 Ніч»): night = dark theme (default); light = `theme-light` class on `<html>` switching the **whole site** to a light theme via CSS variables in `globals.css`. Persisted in `localStorage["ai-ugoda-theme"]`, restored before first paint by inline script in `layout.tsx`.
- Logo: Splash (session, ≤2.2s) + sidebar lockup; duplicate root-layout logo removed.

## 7. Docker
- Services: postgres (pgvector/pgvector:pg16), redis, api, web, worker.
- Healthchecks use Python (API) and Node (Web) — no curl dependency.
- All services healthy.

## 8. Testing & Quality
- Backend: `pytest` → 23 passed, 2 skipped (401 tests target protected `/bookmarks`; `/stats` is public).
- Lint: `ruff check` → 0 errors.
- Frontend: `tsc --noEmit` → 0 errors; `next build` → successful (19 routes).
- Local verification (02.11.2026): all 14 pages + `/three` return 200; `/health` ok; `/stats` returns real numbers (5 acts · 5 revisions · 7 provisions).
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
- `e926cad` docs: update STATUS (scene, theme, public stats, tests).
- `ec92b70` remove duplicate logo from root layout.
- `c109d5f` scene title AI Ugoda · Верховна Рада, light theme toggle, beautiful scene texts, public stats, tests updated.
- `44f5386` K4 real sync wiring + ruff + gitignore.
- `6cd6e67` K12 legal review checklist.
- `f92536e` K7–K12 (JWT, endpoints, migration, AI providers, load tests).
- `da73f6d` fix(K1): auth AND condition, removed dead code import_service, added 401 test, AUDIT report.
- `c381fb5` feat: Hunspell Ukrainian FTS, Redis rate limiter, unique constraints/upserts, branded logo & splash.
- Earlier: PostgreSQL migration, ruff cleanup, status audit.

---
Full history in git log.


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
- ruff 0 errors; tsc 0 errors; next build OK (19 routes); pytest 23 passed / 2 skipped.
- Auth: JWT + RBAC (deps.py), security headers middleware, AUTH_DISABLED flags, rate limiting (Redis + in-memory fallback).
- `/api/v1/stats` public — dashboard shows real numbers without login.
- pgvector + FTS schema (migrations 0003–0005, `ukrainian` config verified).
- Branded logo (Терези рівноваги) + Splash; duplicate root-layout logo removed.
- Interactive 3D scene: «AI Ugoda · Верховна Рада» / «Київ. Площа Конституції», houses around scene removed, day/night → site-wide light/dark theme with localStorage.
- K4 real import: `/sync/run` → `sync_once()` (parses zakon.rada.gov.ua).
- K10 AI providers: mock/groq/openai/anthropic (real provider needs API key in `.env`).
- K11 endpoints: /bookmarks, /monitoring, /contracts (+ migration `516775f2e1d9`, frontend pages).
- Unique constraints + idempotent upserts (nreg, revision, provision).
- Documentation consolidated: STATUS.md, PROJECT_FULL_REPORT.md, OPERATIONS.md (3 files).

## 14. Not Completed / Blocked
- Embedding generation (column exists, data not populated).
- Real LLM provider: needs `GROQ_API_KEY`/`OPENAI_API_KEY`/`ANTHROPIC_API_KEY` in `.env` + `AI_PROVIDER=<name>`.
- K12 legal sign-off: lawyer must fill out the checklist (see STATUS.md §Legal review) — pending.
- Full wiring of some informational pages to live API data (assistant, changes, legal-map, reports).
- Dependency CVEs (pip-audit 98, npm audit 2) — requires dependency updates.

## 15. Errors Fixed
- Auth: `AUTH_DISABLED OR APP_ENV=development` → `AND`; `AUTH_DISABLED=False` default; anonymous user without admin rights.
- Removed dead code in `import_service.py:upsert_force_level`.
- Ruff errors (B008/F821 documented) → 0 errors.
- Docker healthchecks fixed (Python/Node instead of curl).
- Model compatibility with SQLite tests (Vector/TSVECTOR dialect-aware).
- `/api/v1/stats` was 401 for anonymous users → made public; 401 tests moved to protected `/bookmarks`.
- Duplicate root-layout `<Logo size={80}>` removed (duplicated sidebar logo on every page).
- Scene card CSS class mismatch (`iu-sec` → `iu-card-sec`).
