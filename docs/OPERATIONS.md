# AI Ugoda — Експлуатація, запуск, план робіт

**Оновлено:** 12.11.2026. Як запустити, як супроводжувати, що робити далі.  
Стан — `STATUS.md`; архітектура/промти — `PROJECT_FULL_REPORT.md`.

---

## 1. Локальний запуск

```powershell
# 1) Інфраструктура (потрібна ПЕРЕД тестами/e2e — інакше «немає зв'язку з API»)
docker compose up -d postgres redis          # postgres/pgvector + redis:7

# 2) API (:8000)
$env:DATABASE_URL="postgresql+psycopg2://aiugoda:aiugoda@localhost:5432/aiugoda"
$env:AUTH_DISABLED="true"; $env:APP_ENV="development"
cd apps\api
alembic upgrade head                          # CLI alembic, не python -m alembic
python -m uvicorn app.main:app --reload --port 8000

# 3) Web (:3000)  — PowerShell блокує npm.ps1: використовувати npm.cmd/npx.cmd
cd apps\web
npm install
npm.cmd run dev

# 4) Перевірки
cd apps\web; npx.cmd tsc --noEmit; npx.cmd playwright test   # 19 passed
cd ..\..; python -m pytest -q; python -m ruff check .        # 30 passed / clean
```

- **Docker Desktop** має бути запущений; контейнери: `aiugoda_postgres` (має стати `healthy`), `aiugoda_redis`, `api`, `web`, `worker` (заглушка).
- **Dev-сценарій** для e2e: `AUTH_DISABLED=true` + `APP_ENV=development`; API віддає анонімного `dev-user` без admin-прав.
- **PowerShell**: `npm.cmd` / `npx.cmd` / `alembic` (не `python -m alembic`); бінарні операції з git через `cmd /c`.
- Тестові SQLite `*.db` у корені — видаляти перед `pytest` (у `.gitignore`).

## 2. Ключові конфіги

**API — `apps/api/app/core/config.py` (`.env` у корені):**

| Змінна | Default |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://aiugoda:aiugoda@localhost:5432/aiugoda` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `SECRET_KEY` | `dev-secret-change-me` (**у production старт упаде**, якщо не змінити) |
| `AUTH_DISABLED` | `False` (dev: `True`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 10080 (7 днів) |
| `RATE_LIMIT_PER_MINUTE` | 120 |
| `AI_PROVIDER` | `mock` (`mock|groq|openai|anthropic`) |
| `GROQ_/OPENAI_/ANTHROPIC_API_KEY`, `*_MODEL` | `""` / `llama-3.1-8b-instant`, `gpt-4o-mini`, `claude-3-haiku-20240307` |
| `ZAKON_RADA_BASE_URL`, `DATA_RADA_LAWS_LIST_URL` | офіційні хости (білий список) |
| `CORS_ORIGINS` | `http://localhost:3000` |
| `MAX_UPLOAD_MB` / `STORAGE_PATH` / `CONTRACT_RETENTION_DAYS` | 25 / `./data/uploads` / 90 |

**Web:** `NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_APP_ENV` (див. `.env.example`).

## 3. Імпорт джерел (операція)

- **Через UI**: `/uk/admin` → «Запустити синхронізацію» (потрібні admin-права; в dev — `AUTH_DISABLED` не дає admin!) → звіт: тривалість, знайдено/додано/оновлено/помилки, «Не імпортовано» URL+причина, попередження, попередні запуски.
- **Через API**: `POST /api/v1/sync/run` (admin) → фоновий `sync_once()`; спостерігати: `GET /sync/runs?limit=5`, `GET /sync/status` (конектори, `import_locked`, стан джерел).
- **Одноразовий скрипт**: `python apps/api/scripts/run_import_once.py` → JSON-звіт.
- **Одноразові**: `scripts/init_db.py` (create_all без міграцій), `scripts/dev_fixtures.py` (5 фікстур-актів).
- **Обмеження**: один запуск одночасно (`_import_lock`, 409); ≤1 HTTP-запит/с; лише білий список хостів; типовий результат Tier-1: `discovered=13, updated=13, errors=0`.

## 4. Моніторинг і діагностика

| Що | Як |
|---|---|
| Здоровʼя | `GET /health`, `GET /api/v1/health` → `{"status":"ok"}` |
| Логи | uvicorn stdout; журнал імпортів — таблиця `import_runs` + `/sync/runs` |
| Стан джерел | `GET /sync/status` → `active | degraded | down` (≥3 помилки поспіль → `down`) |
| Rate limit | 429 `Rate limit exceeded...`; винятки `/health,/docs,/openapi.json` |
| Аудит | `audit_logs` (записи `source_not_allowed`) |
| Типові збої | Docker не запущений → API 501/timeout → e2e «немає зв'язку з API»; порт 8000 зайнятий старим uvicorn → `Stop-Process`; зіпсований кеш `apps/web/test-results` → видалити перед прогоном; dev-сервер перезапускати після оновлення залежностей |

## 5. CI/деплой

- **CI** (`.github/workflows/ci.yml`, push/PR → `main`): job `web` = `npm ci` + `tsc` + `playwright install chromium`; job `api` = `pip install -r requirements.txt` + `ruff check app` + `alembic upgrade head` + `pytest` (PG16 pgvector-сервіс, `SECRET_KEY=ci-test-...`).
- **Node**: 20 (≥20.9 — вимога Next 16). Python: 3.12 у CI, 3.14 локально.
- **Контейнер API**: `alembic upgrade head && uvicorn ... --host 0.0.0.0:8000`, healthcheck `/health`.
- **Перед production**: змінити `SECRET_KEY`, `AUTH_DISABLED=false`; `.env` не комітиться.

---

## 6. План робіт (що потрібно зробити; пріоритет ↓)

> Перелік сформований за результатами аналізу коду на 12.11.2026. Нові вимоги/план надасть власник після аналізу проєкту.

### P0 — безпека та коректність перед будь-яким запуском
1. ~~**Підключити `verify_citation()` у `ask()`**~~ — ✅ виконано (12.11.2026): `ask()` перевіряє кожну цитату, `confidence` = частка підтверджених, чесний фолбек без мок.
2. **Юридичне рев'ю** чек-листа `PROJECT_FULL_REPORT.md` §9 (ієрархія, ваги індексу уваги, рівні сили, персдані).
3. ~~**Виправити битий блок `globals.css`**~~ — ✅ виконано (12.11.2026).
4. **Вирішити robots.txt `data.rada.gov.ua`** (повага ↔ batch-каталог).
5. **Бейджі походження L0–L4 у UI** (текст закону / знайдено програмою / перевірено правилами / потребує перевірки ШІ).

### P1 — функціональні прогалини
5. **Завантаження файлів** у `/uk/workspace` (`POST` ендпоінт; схема/захист уже є).
6. **Реальний `GET /graph/{id}`** — вузли/ребра з `legal_links` (UI вже готовий, зараз стаб).
7. **`GET/PATCH /conflicts/{id}`** — збереження `conflict_candidates` + підтвердження експертом; реалізувати `SPECIAL_VS_GENERAL` і `CODE_DUPLICATION`.
8. **Підключити `RiskAssessor`** до ендпоінта/UI як «Індекс уваги» (формула готова, ваги затверджує юрист).
9. **Стрім змін** `/uk/changes`: наповнювати `legal_events` з дифів ревізій замість сортування списку.
10. **Воркер розкладу**: замінити `worker`-заглушку на плановий `sync_once()` (cron/beat) + сповіщення про `down`-джерела.

### P2 — якість AI/RAG
11. **LLM-провайдер у прод**: обрати провайдер, ключі, `AI_PROVIDER`, моніторинг помилок (чесний фолбек уже реалізовано).
12. **Обчислення embeddings** (колонка `Vector(1536)` + HNSW вже створені) → гібридний пошук FTS+vector.
13. **`prompt_version`/`ai_analyses`** — почати писати історію запитів й версій промптів.

### P3 — досвід і розширений функціонал
14. Доставка моніторингу (email/Telegram за `delivery_preferences`).
15. Експорт звітів PDF/CSV (`/uk/reports`).
16. Прибрати невикористаний `framer-motion` (або оживити ним мікро-анімації).
17. Ghosting e2e-скриншотів: спробувати headed-прогін у CI (поки що артефакт оточення).
18. Прибрати вороний `scripts/__pycache__/seed_acts...pyc`; `asyncio_mode` у `pytest.ini` — за потреби `auto`.

### Заморожено (рішення власника)
- Юр-рев'ю K12 (п.2), LLM-ключі (п.11), ендпоінт завантаження (п.5), robots.txt (п.4) — усе перелічене вище як задачі; статус — `STATUS.md` §2.1.
