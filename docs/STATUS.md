# AI Ugoda — Статус проєкту (повний звіт)

Дата: 02.11.2026
Автор: Arthur Petrunko <arthurpetrunko@gmail.com>
Гілка: main @ ec92b70 (Remove duplicate logo from root layout)

## 0. Останні зміни (01–02.11.2026)

**Інтерактивна сцена (головна сторінка):**
- Заголовок сцени: **«AI Ugoda · Верховна Рада»** (обидві назви в титулі, як у ТЗ)
- Золотий підзаголовок **«Київ. Площа Конституції»** + ефектний опис: *«Золоті куполи над Дніром — і кожен камінь площі веде до розділу законодавства»*
- Текст підказки та aria-label сцени відшліфовано
- Сусідній будинок і дальній будиночок навколо сцени **прибрано**
- Виправлено баг: CSS-клас секції картки (`iu-sec` → `iu-card-sec` не збігався з стилями)

**День/Ніч → тема всього сайту:**
- Кнопка сцени: **«☀ Світла» / «🌙 Ніч»**
- «Ніч» — темна тема (як було): темне меню, темна сцена
- «Світла» — клас `theme-light` на `<html>`, **весь сайт** перемикається на світлу тему (фон, меню, картки, таблиці, інпути, модалки, хедлери, скелетони) через CSS-змінні у `globals.css`
- Вибір зберігається в `localStorage` (`ai-ugoda-theme`) і відновлюється inline-скриптом у `layout.tsx` до першого рендеру — без спалаху темної теми

**Логотип:**
- Прибрано **повторне лого** `<Logo size={80}>` із `layout.tsx` (дублювало лого в сайдбарі на кожній сторінці); лишились заставка + лого в меню

**Статистика:**
- `/api/v1/stats` зроблено **публічним** (без JWT) — картка «Стан даних» і чип у хедері показують реальні числа без логіну
- Поточні значення БД: **5 актів · 5 редакцій · 7 статей**

**Локальна перевірка (02.11.2026):**
- Усі 14 сторінок (+ `/three`) відповідають **200**
- API: `/health` → ok; `/stats` → реальні числа; `/documents` → список
- Якість: `ruff` — 0 помилок; `tsc --noEmit` — 0 помилок; `next build` — успішно; `pytest` — **23 passed, 2 skipped** (тести 401 переведено на захищений `/bookmarks`, бо `/stats` тепер публічний)
- Коміти: `f92536e` (K7–K12), `6cd6e67` (чек-лист), `44f5386` (K4 sync), `c109d5f` (сцена + тема + публічний stats), `ec92b70` (повторне лого)

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
- `components/InteractiveScene.tsx` — інтерактивна Three.js сценка «AI Ugoda · Верховна Рада» / «Київ. Площа Конституції» на головній
- День/ніч: «☀ Світла» / «🌙 Ніч» — перемикає **світлу/темну тему всього сайту** (`theme-light` + localStorage)
- Рухомі об'єкти (автівки, люди, пропливи, прапори), клік по об'єкту відкриває розділ сайту
- Будинки навколо сцени прибрано; повторне лого з `layout.tsx` прибрано

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
- Ендпоінт `/api/v1/stats` (documents, revisions, provisions, links) — **публічний**, без JWT (щоб дашборд показував реальні числа)
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
| K4 | Реальний імпорт Tier 1 | ✅ Виконано | /sync/run запускає sync_once(): парсинг zakon.rada.gov.ua + import_parsed_document; nreg КУпАП `80731-10` |
| K10 | ШІ / RAG-анализи | ⚠️ Частково | AI_PROVIDER=mock за замовчуванням; реальні провайдери (groq/openai/anthropic) підтримуються, але не підключені (немає ключів) |
| K11 | Акаунти, моніторинг, договори | ✅ Виконано (API) | Ендпоінти /bookmarks, /monitoring, /contracts, міграція 516775f2e1d9, JWT авторизація |
| K12 | Якість і право | ⚠️ Частково | Тести pytest 23 passed (включаючи 3 навантажувальні); юридичне рев'ю не проведено |

## 3. Технічні деталі

### 3.1 Логотип і сцена (K2)
- `components/brand/Logo.tsx` — variants: `mark` / `lockup` / `seal`
- `components/brand/Splash.tsx` — заставка (SessionStorage, 2.2с)
- `app/icon.svg` — SVG логотип (160×160, scales)
- `components/InteractiveScene.tsx` — інтерактивна Three.js сценка: титул «AI Ugoda · Верховна Рада», місце «Київ. Площа Конституції», 7 гарячих зон → розділи сайту
- Тема: `document.documentElement.classList.toggle("theme-light")` + `localStorage["ai-ugoda-theme"]`; inline-скрипт у `layout.tsx` відновлює тему до рендеру
- Підключено: `layout.tsx` (заставка), `shell.tsx` (лого меню), `uk/page.tsx`, `three/page.tsx` (сценка)

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
- Тести 401 перевірено на `/api/v1/bookmarks` (захищений); `/api/v1/stats` тепер публічний
- ruff: 0 помилок; tsc --noEmit: 0 помилок; next build: успішно
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
| `components/InteractiveScene.tsx` | Інтерактивна 3D сценка + день/ніч → тема сайту |
| `styles/globals.css` | CSS-змінні теми + світла тема (`.theme-light`) |
| `app/layout.tsx` | Кореневий layout: заставка, скрипт відновлення теми (повторне лого прибрано) |
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
- **Останній коміт:** `ec92b70` (Remove duplicate logo from root layout)
- **Ключові коміти:** `f92536e` (K7–K12), `44f5386` (K4 sync), `c109d5f` (сцена + світла тема + публічний stats), `ec92b70` (повторне лого)
- **Робоче дерево:** чисте, запушено в origin/main

---

**Дата:** 02.11.2026
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
