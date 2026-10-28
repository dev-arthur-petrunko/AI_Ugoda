# AI Ugoda — всесвідомлюючий проєктний документ

**Версія проєкту:** 0.1.0
**Дата:** 26.10.2026
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
**Гілка:** `main` @ `da73f6d` (запушений у `origin/main`)
**Репозиторій:** `https://github.com/dev-arthur-petrunko/AI_Ugoda`

---

## 1. Огляд проєкту

AI Ugoda — **«Навігатор і детектор небезпеки над законодавством України»**. Це не ще одна база законів (така вже є — zakon.rada.gov.ua), а інтелектуальна платформа поверх неї, яка:

1. Показує закон **на будь-яку дату** (як він виглядав вчורך / рік тому).
2. Показує, **з чим колідує і хто кого перебиває** (ієрархія юридичної сили).
3. Виділяє **головне та небезпечне** (штрафи, строки, заборони, кримінальна відповідальність) мовою людини.
4. Відповідає на питання **тільки з посиланнями** на акти та статті.

**Головне правило:** ніколи не вигадуємо закон. Кожне твердження = посилання на акт + статтю + дату редакції. Джерела не знайдено — пишемо «не знайдено в базі».

## 2. Архітектура (монOREPO)

```
C:\Users\Arthur\Desktop\AI Ugoda\
├── apps/
│   ├── api/                  # Backend (FastAPI, Python 3.14)
│   │   ├── app/
│   │   │   ├── api/v1/
│   │   │   │   ├── endpoints/  # documents, stats, sync, health
│   │   │   │   └── api.py
│   │   │   ├── api/deps.py     # автентифікація, БД-сесія
│   │   │   ├── core/
│   │   │   │   ├── config.py   # налаштування (pydantic-settings)
│   │   │   │   └── database.py # SQLAlchemy engine/сесія
│   │   │   ├── middleware/
│   │   │   │   └── rate_limit.py (Redis + in-memory fallback)
│   │   │   ├── models/         # SQLAlchemy ORM (17 таблиць)
│   │   │   └── services/
│   │   │       ├── import_service.py   # ідемпотентний upsert
│   │   │       ├── search.py           # SearchService (LIKE / tsquery)
│   │   │       ├── connector.py        # DataRada + ZakonRada
│   │   │       ├── parser.py           # ZakonRadaParser (HTML)
│   │   │       └── conflict_engine.py  # детектор колізій
│   │   ├── alembic/versions/ # 0001…0005
│   │   ├── requirements.txt
│   │   └── pyproject.toml    # ruff конфігурація
│   └── web/                  # Frontend (Next.js 14.2.15, App Router)
│       ├── src/
│       │   ├── app/uk/         # сторінки (/ , /admin, /legislation, ...)
│       │   ├── components/
│       │   │   ├── brand/      # Logo.tsx, Splash.tsx
│       │   │   ├── nav/        # sidebar.tsx
│       │   │   ├── reference/  # shell.tsx
│       │   │   └── ui/         # loader.tsx, empty-state, button
│       │   ├── lib/api.ts      # типізований API-клієнт
│       │   └── styles/         # globals.css, logo.css
│       ├── public/             # favicon.ico
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       └── package.json
├── docker/
│   └── postgres/
│       ├── Dockerfile        # pgvector/pgvector:pg16 + hunspell-uk
│       └── init/
│           └── 01_ukrainian_fts.sql
├── docker-compose.yml        # postgres, redis, api, web, worker
├── .env.example
├── .gitignore
├── pytest.ini
└── docs/                     # документація (див. розділ 15)
```

**Стек:**
|Чарівник|Технологія|
|--------|----------|
|Backend|FastAPI + SQLAlchemy 2.0 + Alembic + psycopg2-binary + httpx + beautifulsoup4|
|Frontend|Next.js 14.2.15 + React 18 + TypeScript + Tailwind + Framer Motion + Lucide|
|База даних|SQLite (dev) / PostgreSQL 16 + pgvector + pg_trgm (продакшн через Docker)|
|Кеш/Rate limit|Redis 7-alpine + in-memory fallback|
|Контейнеризація|Docker Compose (5 сервісів)|
|Тести|pytest (backend), npm build (frontend)|


## 3. База даних та міграції

### 3.1 Поточний стан (dev)
- **Тип:** SQLite (один файл `data/aiugoda.db`, `.gitignore` криє `data/`)
- **Зміна:** 5 актів, 10 редакцій, 14 положень, 0 зв'язків, 0 посилань
- **Джерела:** тільки `zakon.rada.gov.ua` (дотримано Д9 — тексти актів лише з офіційного державного ресурсу)
- **Виявлені проблеми:** КУпАП має `nreg=807-V` (очікується `80731-10`); кожен акт має 2 ідентичні редакції (однаковий `source_hash`) — дублі

### 3.2 Alembic міграції
|Міграція|Опис|
|--------|-----|
|`0001_initial_schema`|Початкова схема (акти, ревізії, положення, рівні сили, зв'язки)|
|`0002_extend_schema`|Розширення схеми (події, посилання, колізії, користувачі, моніторинг, договори)|
|`0003_pgvector_fts`|pgvector + pg_trgm, `search_vector tsvector`, `embedding vector(1536)`|
|`0004_unique_constraints`|UNIQUE на `legal_documents.nreg`, `document_revisions(document_id,effective_from)`, `legal_provisions(revision_id,provision_identifier)` + дедуп перед обмеженням|
|`0005_ukrainian_fts`|Переключення `search_vector` на конфігурацію `ukrainian` (Hunspell), GIN індекс|

### 3.3 Основні таблиці
`legal_document`, `document_revision`, `legal_provision`, `legal_force_level`, `legal_link`, `legal_reference`, `legal_event`, `ai_analysis`, `conflict_candidate`, `user`, `user_monitoring_rule`, `user_bookmark`, `contract_document`, `contract_analysis`, `audit_log`.

## 4. API-ендпоінти (`/api/v1`)

|Метод|Шлях|Опис|Авторизація|
|-----|-----|-----|-----------|
|GET|`/health`|Статус сервісу|ν/nē|
|GET|`/api/v1/stats`|Лічильники (акти, ревізії, положення, зв'язки)|Токен|
|GET|`/api/v1/documents`|Список/пошук (`q`, фільтри, пагінація)|Токен|
|GET|`/api/v1/documents/suggestions?q=`|Автодоповнення назв|Токен|
|GET|`/api/v1/documents/search/by-provision?provision_ref=`|Пошук за статтею («Стаття 625 ЦК»)|Токен|
|GET|`/api/v1/documents/{id}`|Картка акта|Токен|
|GET|`/api/v1/documents/{id}/provisions`|Дерево статей|Токен|
|GET|`/api/v1/documents/{id}/revisions`|Список редакцій|Токен|
|GET|`/api/v1/documents/{id}/at?date=`|Акту на дату (time-travel)|Токен|
|GET|`/api/v1/sync/status`|Статус коннекторів|ν/nē|
|POST|`/api/v1/sync/run`|Запуск синхронізації (тільки адмін)|Адмін|

**Автентифікація:** анонімний доступ дозволено лише якщо `AUTH_DISABLED=true` і `APP_ENV=development` (і не інакше). Анонімний користувач — `is_superuser: False`, роль `user`. Усі інші випадки → 401. У продакшені `SECRET_KEY=dev-secret-change-me` і `AUTH_DISABLED=true` блокують старт.

## 5. Безпека

|Засіб|Статус|Деталі|
|-----|------|------|
|CORS|✅|Тільки `http://localhost:3000`|
|SQL-ін'єкції|✅|Параметризовані запити SQLAlchemy (`text()` з `:params`)|
|Автентифікація|⚠️|Заглушка (simple token), `AUTH_DISABLED=False` за замовчуванням|
|Rate limiting|✅|Per IP, sliding window 60с, 120 req/min, Redis primary + in-memory fallback, `EXEMPT_PATHS` = `/health, /, /docs, /openapi.json, /redoc`|
|SECRET_KEY перевірка|✅|У продакшені не дозволяється `dev-secret-change-me`|
|JWT / RBAC|❌|Не реалізовано (план: Етап 4)|
|CSRF / CSP|❌|Потрібно додати|

## 6. Пошук

`SearchService` dialect-aware:

- **PostgreSQL:** `plainto_tsquery('ukrainian', :fts)` + GIN індекс на `search_vector` + Hunspell словник `uk_UA`.
- **SQLite (dev):** `LIKE` по `title`, `normalized_text`, `provision_text`.

Фільтри: тип документу, статус, орган, дати прийняття, рівень юридичної сили, `only_current`. Розпізнавання посилань на статтю через regex (`стаття N` / `article N`).

**Важливо:** українська FTS конфігурація `ukrainian` реалізована в міграціях і Docker-образі (`docker/postgres/Dockerfile` ставить `hunspell-uk`), але **не перевірена наживо** через відсутність Docker Desktop у цьому середовищі.

## 7. Імпорт даних та коннектори

### 7.1 Джерела (Д9 — лише офіційні державні)
|Джерело|URL|Роль|
|-------|-----|-----|
|data.rada.gov.ua|`/ogd/zak/laws/list.json`|Основне — метадані, картки актів (JSON, оновлення щогодини)|
|zakon.rada.gov.ua|`/laws/main/...`|Запасне — тексти актів (HTML парсинг, CC BY 4.0)|

**Білий список хостів:** лише `data.rada.gov.ua` і `zakon.rada.gov.ua`. Будь-яка спроба імпорту з іншого хоста → `SourceNotAllowed`, запис у `audit_logs`, імпорт зупиняється.

### 7.2 ImportService
- Ідемпотентний upsert (`ON CONFLICT` логіка): документ за `nreg`, ревізія за `(document_id, effective_from)`, положення за `(revision_id, provision_identifier)`.
- Контрольні суми SHA-256 (`source_hash`, `source_checksum`, `content_checksum`).
- Карантин для підозрілих розборів (парсер не вдався → `None`, не публікується).
- Блокування паралельної синхронізації.

## 8. Фронтенд (Next.js 14)

### 8.1 Сторінки (`/uk/`)
|Маршрут|Статус даних|
|-------|------------|
|`/`|Головна (пошук, карточки функцій)|
|`/uk`|Дашборд — реальні лічильники з `/api/v1/stats`|
|`/uk/legislation`|Пошук актів — реальний з `/api/v1/documents?q=`|
|`/uk/legislation/[documentId]`|Картка акта — дерево статей, редакції, «на дату»|
|`/uk/admin`|Адмінка — `/sync/status`, `/sync/run`|
|`/uk/assistant`|⚠️ Placeholder|
|`/uk/changes`|⚠️ Placeholder|
|`/uk/contracts`|⚠️ Placeholder|
|`/uk/conflicts`|⚠️ Placeholder|
|`/uk/legal-map`|⚠️ Placeholder|
|`/uk/monitoring`|⚠️ Placeholder|
|`/uk/reports`|⚠️ Placeholder|
|`/uk/settings`|⚠️ Placeholder|
|`/uk/workspace`|⚠️ Placeholder|

9 сторінок-плейсхолдерів потребують довобудби за шаблоном «Поки що порожньо» (ТЗ, Крок 3б.3).

### 8.2 Дизайн-система
- **Палитра:** чорний `#080605`, шоколад `#1B120C`/`#2E1D12`, золото `#8F6F2B`/`#C9A24B`/`#E8C871`, крем `#F1E8D8`.
- **Шрифти:** Playfair Display (заголовки), Cormorant Garamond (курсив акцент), Inter (UI), Source Serif 4 (текст закону), JetBrains Mono (номери, дати).
- **Ефект:** скляні панелі (glassmorphism), матове скло, золотий акцент.

## 9. Логотип і бренд (Д15)

- **Знак:** «Терези рівноваги» — дві чаши, балка, ромб-печатка.
- **Компонент:** `components/brand/Logo.tsx` — варіанти `mark` / `lockup` / `seal`, розмір задається явно (`size`), анімація кількування балки (`animated`).
- **Заставка:** `components/brand/Splash.tsx` — показується один раз за сесію (`sessionStorage`), ≤ 2.2 с, пропускається кліком.
- **Підключено:** `layout.tsx` (Splash, шрифти), `sidebar.tsx` (lockup), `shell.tsx` (mark), `loader.tsx` (mark 128 px), `favicon.ico`.
- **Стилі:** `styles/logo.css` (кейфрейми `lgdraw`, `lgpop`, `lgset`, `lgspin`, `splashout`).
- **Примітка:** 9 скріншотів місць розміщення логотипу не зроблено (веб-сервер не запускався без PostgreSQL).

