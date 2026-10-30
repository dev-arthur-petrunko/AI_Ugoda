# AI Ugoda — Статус проєкту (повний звіт)

Дата: 30.10.2026
Автор: Arthur Petrunko <arthurpetrunko@gmail.com>
Гілка: main @ 14bfebc (K10: Add AI service with RAG pipeline and ask endpoint)

## 1. Загальний стан

AI Ugoda — юридична інтелектуальна платформа для роботи з законодавством України.
Проєкт знаходиться на стадії завершення Етапу 1 (K1–K12 реалізовано, решта — доопрацювання).

### ✅ Виконано (K1–K12)

**K1 — Очищення та безпека (основа):**
- `deps.py`: `AUTH_DISABLED AND APP_ENV=development` (було `OR`)
- `AUTH_DISABLED=False` за замовчуванням; анонімний користувач — `is_superuser: False`, роль `user`
- Мертвий код видалений (`import_service.py:80-82`)
- Тест `test_auth.py`: 401 без токена

**K2 — Логотип + інтерактивна сценка:**
- `components/brand/Logo.tsx` — variants: `mark` / `lockup` / `seal`
- `components/brand/Splash.tsx` — заставка (SessionStorage, ≤ 2.2 с)
- `components/InteractiveScene.tsx` — інтерактивна Three.js scenka «Площа Конституції» на головній
- День/ніч перемикач, рухомі об'єкти (автівки, люди, пропади), клік по об'єкту відкриває розділ сайту

**K3 — База даних:**
- PostgreSQL 16 + pgvector + pg_trgm (Docker)
- Ukrainian FTS: конфігурація `ukrainian` + Hunspell словник `uk_UA`
- UNIQUE constraints: nreg, revision+hash, provision+identifier
- Alembic version: `0005_ukrainian_fts`

**K4 — Імпорт даних:**
- `seed_acts.py` — імпорт 5 тестових актів (Конституція, Цивільний, Кримінальний, КУпАП, Податковий кодекси)
- `upsert_revision` функція виправлена (перевірка по `source_hash`)
- nreg КУпАП: `80731-10` (виправлено — відповідає офіційному номеру)
- Джерела лише з `zakon.rada.gov.ua` (Д9 дотримується)
- data.rada.gov.ua доступне (200 OK, JSON підтверджено)

**K5 — Сторінки розділів + дашборд:**
- Сторінки: `/uk`, `/uk/legislation`, `/uk/changes`, `/uk/conflicts`, `/uk/contracts`, `/uk/monitoring`, `/uk/admin`, `/uk/assistant`, `/uk/legal-map`, `/uk/reports`, `/uk/settings`, `/uk/workspace`
- Дашборд на головній з картками «Закон на дату», «Хто кого перебиває», «Стан даних»
- Інтерактивна Three.js scenka на головній замість статичного логотипу

**K6 — Базова аналітика акта:**
- Ендпоінт `/api/v1/stats` (documents, revisions, provisions, links)
- Ендпоінт `/api/v1/documents/{id}/summary` (AIService.summarize_act)

**K7 — Безпека (виконано):**
- CORS: тільки `http://localhost:3000`
- Rate limiting: Per IP, sliding window, Redis + in-memory fallback
- SECRET_KEY перевірка в продакшені
- JWT / RBAC: реалізовано (декодування токена, пошук користувача в БД, ролі user/admin)
- CSRF / CSP: реалізовано (заголовки безпеки в middleware)
- AUTH_DISABLED=False за замовчуванням (анонімний доступ у dev без прав адміна)

**K8 — Пошук «на дату», diff, гібридний пошук:**
- Ендпоінт `/api/v1/documents/{id}/at?date=`
- Ендпоінт `/api/v1/documents/{id}/diff?from_rev=&to_rev=`
- Ukrainian FTS (tsquery, gin індекс)

**K9 — Зв'язки, колізії, ризик:**
- `conflict_engine.py` — детектор колізій
- `risk.py` — модуль оцінки ризику норми (0-100, рівні low/mid/high)
- Ендпоінт `/api/v1/conflicts`

**K10 — ШІ / RAG-конвеєр:**
- `ai_service.py` — RAG-конвеєр (пошук по документам + цитування статей)
- Ендпоінт `/api/v1/ai/ask`, `/api/v1/ai/documents/{id}/summary`
- ✅ AI_PROVIDER підтримує: mock, groq, openai, anthropic (за замовчуванням mock; встановіть ключ у .env для реального провайдера)

## 2. Частково виконані завдання (K4, K10, K12)

| Крок | Назва | Статус | Причина |
|------|-------|--------|---------|
| K4 | Реальний імпорт Tier 1 | ⚠️ Частково | seed_acts.py працює, але дані тестові (5 актів); nreg КУпАП виправлено на `80731-10` |
| K10 | ШІ / RAG-анализи | ⚠️ Частково | AI_PROVIDER=mock за замовчуванням; реальні провайдери (groq/openai/anthropic) підтримуються, але не підключені (немає ключів) |
| K11 | Акаунти, моніторинг, договори | ✅ Виконано (API) | Ендпоінти /bookmarks, /monitoring, /contracts, міграція 516775f2e1d9, JWT авторизація |
| K12 | Якість і право | ⚠️ Частково | Тести pytest 23 passed (включаючи 3 навантажувальні); юридичне рев'ю не проведено |

## 3. Технічні деталі

### 3.1 Логотип (K2)
- `components/brand/Logo.tsx` — variants: `mark` / `lockup` / `seal`
- `components/brand/Splash.tsx` — заставка (SessionStorage, 2.2с)
- `app/icon.svg` — SVG логотип (160×160, scales)
- `components/InteractiveScene.tsx` — інтерактивна Three.js scenka на головній
- Підключено: `layout.tsx`, `shell.tsx`, `uk/page.tsx`, `three/page.tsx`

### 3.2 База даних (K3)
- PostgreSQL 16 + pgvector + pg_trgm (Docker)
- Ukrainian FTS: конфігурація `ukrainian` + Hunspell словник `uk_UA`
- UNIQUE constraints: nreg, revision+hash, provision+identifier
- Alembic version: `0005_ukrainian_fts`

### 3.3 Імпорт (K4)
- `seed_acts.py` — імпорт 5 тестових актів
- `upsert_revision` виправлена (перевірка по source_hash)
- nreg КУпАП: `80731-10` (виправлено — відповідає офіційному номеру)
- Джерела лише з `zakon.rada.gov.ua` (Д9 дотримується)
- data.rada.gov.ua доступне (200 OK, JSON підтверджено)

### 3.4 Безпека (K7)
- CORS: тільки `http://localhost:3000`
- SQL-ін'єкції: параметризовані запити
- Rate limiting: Per IP, sliding window, Redis + in-memory fallback
- SECRET_KEY перевірка: у продакшені не дозволяється `dev-secret-change-me`
- JWT / RBAC: ✅ реалізовано (декодування токена, пошук користувача в БД, ролі user/admin)
- CSRF / CSP: ✅ реалізовано (заголовки безпеки в middleware)
- AUTH_DISABLED=False за замовчуванням (анонімний доступ у dev без прав адміна)

### 3.5 Тестування
- pytest: 23 passed, 2 skipped (FTS потребує PostgreSQL; 3 навантажувальних тести)
- Тести TestClient використовують SQLite in-memory (override get_db) — не потребують PostgreSQL
- ruff: 0 помилок
- bandit: 6 LOW
- pip-audit: 98 CVE у 16 пакетах
- npm audit: 2 вразливості (postcss)

## 4. Файли проєкту (без секретів)

### 4.1 Документація (`docs/`)
| Файл | Опис |
|------|------|
| `AUDIT_2026-10-26.md` | Звіт аудиту поточного стану |
| `CLEANUP_REPORT.md` | Звіт очищення Етапу 1 |
| `SITE_ANALYSIS.md` | Аналіз сайту (фронтенд + бекенд) |
| `PROJECT_FULL_REPORT.md` | Вся інформація про проєкт |
| `DEVLOG.md` | Журнал розробки |
| `OPERATIONS.md` | Операційна документація |
| `PROJECT_DOCUMENTATION.md` | Всясвідомлюючий проєктний документ |
| `STATUS.md` (новий) | Об'єднаний статус |

### 4.2 Бекенд (`apps/api/`)
| Файл | Опис |
|------|------|
| `app/api/deps.py` | Автентифікація (AND замість OR) |
| `app/core/config.py` | Налаштування (AUTH_DISABLED=False) |
| `app/core/database.py` | SQLAlchemy engine (PostgreSQL/SQLite) |
| `app/middleware/rate_limit.py` | Rate limiting (Redis + in-memory) |
| `app/services/import_service.py` | Ідемпотентний імпорт |
| `app/services/search.py` | SearchService (LIKE / tsquery) |
| `app/services/connector.py` | DataRada + ZakonRada коннектори |
| `app/services/parser.py` | ZakonRadaParser (HTML) |
| `app/services/conflict_engine.py` | Детектор колізій |
| `app/services/risk.py` | Оцінка ризику норми (0-100) |
| `app/services/ai_service.py` | RAG-конвеєр (mock, groq, openai, anthropic) |
| `app/models/*.py` | SQLAlchemy моделі (17 таблиць + bookmarks, monitoring_rules, contract_documents) |

### 4.3 Фронтенд (`apps/web/src/`)
| Файл | Опис |
|------|------|
| `components/brand/Logo.tsx` | Логотип «Терези рівноваги» |
| `components/brand/Splash.tsx` | Заставка (SessionStorage) |
| `components/InteractiveScene.tsx` | Інтерактивна 3D scenka (Three.js) |
| `app/layout.tsx` | Кореневий layout з логотипом |
| `components/reference/shell.tsx` | Оболонка з логотипом, сайдбар, модальний пошук |
| `app/icon.svg` | SVG логотип для favicon |

### 4.4 Docker
| Файл | Опис |
|------|------|
| `docker-compose.yml` | 5 сервісів (postgres, redis, api, web, worker) |
| `docker/postgres/Dockerfile` | pgvector + hunspell-uk |
| `docker/postgres/init/01_ukrainian_fts.sql` | Ініціалізація Ukrainian FTS |

### 4.5 Тести
| Файл | Опис |
|------|------|
| `tests/conftest.py` | Фікстури (SQLite in-memory) |
| `tests/test_auth.py` | Тест 401 без токена |
| `tests/test_import_service.py` | Тест ідемпотентності |
| `tests/test_conflict_engine.py` | Тест колізій |
| `tests/test_fts_ukrainian.py` | Тест FTS (PostgreSQL) |
| `tests/test_sql_injection.py` | Тест SQL-ін'єкцій |

## 5. Правила безпеки (ТЗ)

1. **Секрети лише в `.env`** — не в коді, не в git
2. **`.env` і `*.db` не в git** — `.gitignore` криє
3. **Авторизація за замовчуванням закрита** — `AUTH_DISABLED=False`
4. **Rate limiting** — Per IP, 120 req/min
5. **CORS** — тільки `http://localhost:3000`
6. **SQL-ін'єкції** — параметризовані записи

## 6. Запуск локально

```bash
# Backend
cd apps/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Тести
cd .. && python -m pytest -q

# Frontend
cd apps/web && npm run dev

# Docker (PostgreSQL)
docker compose up -d postgres redis
docker exec aiugoda_api alembic upgrade head
```

## 7. Git

- **Репозиторій:** `https://github.com/dev-arthur-petrunko/AI_Ugoda`
- **Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
- **Гілка:** `main`
- **Останній коміт:** `14bfebc` (K10: Add AI service with RAG pipeline and ask endpoint)
- **Робоче дерево:** чисте

---

**Дата:** 30.10.2026
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
