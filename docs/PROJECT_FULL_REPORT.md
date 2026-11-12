# AI Ugoda — Повний звіт: архітектура, інтерфейс, аналізи, промти

**Оновлено:** 12.11.2026. Усе про проєкт: стек, бекенд, схему БД, інтерфейс, анімації, 3D-сцену, як працюють аналізи й обчислення, повні тексти AI-промптів, безпека, тести.  
Стан і беклог — у `STATUS.md`; запуск і супровід — в `OPERATIONS.md`.

---

## 1. Стек і структура

```
AI Ugoda/
├── apps/api        FastAPI + SQLAlchemy 2 + Alembic (Python 3.14; CI — 3.12)
├── apps/web         Next.js 16.4.6 (App Router) + React 18 + TS 5.5 + Tailwind 3.4
├── tests/           pytest (8 файлів + fixtures: 2 HTML, 1 JSON)
├── docker/          postgres (pgtrgm, pgvector, hunspell-uk) + redis
├── docker-compose.yml  postgres, redis, api, web, worker (заглушка)
├── .github/workflows/ci.yml  два jobs: web (tsc) + api (ruff, alembic, pytest)
└── docs/            STATUS.md · PROJECT_FULL_REPORT.md · OPERATIONS.md
```

- **API** — Uvicorn, префікс `/api/v1`, OpenAPI `/api/v1/openapi.json`; проксі з фронта: rewrite `/api/:path*` → `NEXT_PUBLIC_API_URL`.
- **БД**: PostgreSQL 16 + pgvector + pg_trgm + український FTS (`ukrainian_hunspell`/`ukrainian` TS); SQLite-fallback для тестів.
- **Redis**: rate-limit (ZSET sliding window) з in-memory фолбеком.

---

## 2. Схема бази даних (19 таблиць)

| Таблиця | Ключові поля |
|---|---|
| `users` | email UQ, bcrypt `hashed_password`, `is_active`, `is_superuser` |
| `legal_documents` | `source_id` UQ, `nreg` UQ, title, тип, номер, `adoption_date`, `legal_force_level`, `data_origin` (`official|fixture`), `source_url`, статус |
| `document_revisions` | `effective_from/to`, `source_host`, `source_checksum` (raw SHA-256), `source_hash` (normalized SHA-256), `normalized_text`, `parser_version`, `verification_status`; **UQ(doc, effective_from)**, **UQ(doc, source_hash)** |
| `legal_provisions` | `provision_identifier` UQ на редакцію, ієрархія `parent_provision_id`, `article/part/point/subpoint_number`, `heading`, `text`, `ordinal`, `content_checksum`; **`embedding Vector(1536)`** + **`search_vector` tsvector** (генерований) |
| `legal_links` | типи `amends|repeals|refers_to|implements|interprets|harmonizes_with`, `evidence_text`, `resolution_status` |
| `legal_force_levels` | 8 рівнів: Конституція 100 · Міжн. договори 90 · Закони/кодекси 80 · Постанови ВР 70 · Укази П 60 · ПКМУ 50 · Накази мін-в 40 · Місцеві 30 |
| `legal_events`, `legal_references` | події змін; міжактові посилання (заповнюються частково) |
| `conflict_candidates` | `conflict_type`, `confidence`, `rule_applied`, `winner_provision_id`, `explanation`, `review_status` |
| `import_runs` | журнал імпортів: `status`, лічильники, `report_json` |
| `ai_analyses`, `audit_logs` | аналізи AI (ще не пишуться); аудит-лог (зокрема `source_not_allowed`) |
| `user_bookmarks`, `user_monitoring_rules` | закладки; правила моніторингу (`rule_configuration`, `delivery_preferences` JSON) |
| `contract_documents`, `contract_analyses` | `secure_storage_key`, `file_metadata`, `retention_policy="configurable"`, soft delete `deleted_at` |

**Alembic (10 ревізій):** `0001` базова схема + trgm → `0002` сили/зв'язки → `0003` pgvector+HNSW+tsvector → `0004` унікальні обмеження → `0005` український FTS (hunspell) → `516775f2e1d9` закладки/моніторинг/договори (K11) → `s3dataorigin` → `s3sources` (+`import_runs`) → `s3revcontent` (UQ doc+source_hash).

---

## 3. Бекенд: ендпоінти

| Група | Маршрути | Доступ |
|---|---|---|
| Health | `GET /`, `/health`, `/api/v1/health` | публічні |
| Sync | `POST /sync/run` (старт фонового імпорту), `GET /sync/runs?limit`, `GET /sync/status` | run — **admin**; інші публічні |
| Stats | `GET /stats` — лічильники + `documents_official/fixture/has_official` | публічні |
| Documents | `GET /documents` (q, type, status, authority, дати, `legal_force_level`, `include_fixtures`, `only_current`, limit/offset), `/documents/suggestions`, `/documents/search/by-provision`, `GET /documents/{id}`, `/{id}/quality`, `/{id}/provisions`, `/{id}/revisions`, `/{id}/at?date=` | публічні (читання) |
| Analysis / Diff | `GET /documents/{id}/analysis`, `GET /documents/{id}/diff?from_rev&to_rev` | публічні |
| AI | `POST /ai/ask {question, document_id?}`, `GET /ai/documents/{id}/summary` | авторизація |
| Conflicts | `GET /conflicts/` (on-the-fly `run_all`), `GET|PATCH /conflicts/{id}` — **стаб** | авторизація |
| Graph | `GET /graph/{id}?depth=2` — **стаб** (порожній граф) | авторизація |
| Bookmarks | `GET/POST/DELETE /bookmarks` | активний користувач |
| Monitoring | `GET/POST/DELETE /monitoring` | активний користувач |
| Contracts | `GET /contracts`, `GET/DELETE /contracts/{id}` (soft delete) | активний користувач |
| Auth | `POST /auth/token`, `/auth/register`, `/auth/refresh` | публічні |

---

## 4. Як працюють аналізи та обчислення

### 4.1 Імпорт і парсинг (детермінована конвеєрна логіка)
1. **Вибірка**: Tier-1 = 13 `.frame`-URL на `zakon.rada.gov.ua` (Конституція 254к/96-вр, ЦК 435-15, ГК, КК, КУпАП, ПК, КЗпП, СК, ЗК, КПК, ЦПК, ГПК, КАС) + каталог `data.rada.gov.ua/ogd/zak/laws/list.json`.
2. **Захист**: `validate_url` на етапах `request` і `write`; білий список лише `https` + 2 хости; ≤1 запит/с; ретраї `2**attempt` backoff; raw-кеш `sha256(url)`; стан джерела (3 відмови поспіль → `down`).
3. **Парсер** (`parser.py`): CSS-селектори `h1.law-title`, `div.law-article`; регулярки типів: `Стаття N`, `Частина перша|N`, `Пункт N`, `Підпункт`, `Розділ IVXLC`, `Глава N`; дати `dd.mm.yyyy` / українські родові; dedup змісту змісту (TOC `a.stru`); преобхідні `ordinal`; `content_checksum` = перші 32 hex SHA-256 від `number|title|text`.
4. **Збереження**: `upsert_document` (за `source_id`, фолбек — `nreg`); `upsert_revision` — **S3.7**: однаковий `source_hash` при різній даті → без нової редакції, але `record_warning`; `upsert_provision` унікальний на редакцію; рівень сили з типу акта.
5. **Звіт**: `import_runs.report_json = {stats, parse_errors, duration_sec, failed[], warnings[]}` — його UI показує в адмінпанелі.

### 4.2 Пошук (FTS)
- PostgreSQL: `title ILIKE` **або** `search_vector @@ plainto_tsquery('ukrainian', q)`; `search_vector` — generated `to_tsvector('ukrainian', heading||text)` + GIN; конфіг `ukrainian` = копія `simple` + hunspell-словник.
- SQLite (тести): `LIKE` по title/normalized_text/тексту положень.
- Дефолт: `data_origin='official'` (фікстури — за прапорцем); `only_current` → `effective_to IS NULL OR >= now`; ранжування статичне (`rank=1.0`), сортування за датою.

### 4.3 Колізії (`conflict_engine.py`, детерміновано, без LLM)
- `_force_priority`: 8 рівнів → 1..8.
- **HIERARCHY_CONFLICT** (lex superior): нижчий пріоритет програє; рівні → не конфлікт; `confidence=medium`.
- **SAME_LEVEL_NEWER** (lex posterior): той самий рівень, пізніша дата редакції перемагає; `confidence=high`.
- **DEAD_REFERENCE**: лінк на неіснуючу норму; `confidence=high`.
- **EXPIRING**: `is_temporary | valid_until_condition | effective_to`; `confidence=high`.
- **GHOST_NORM**: акт вимагає неіснуючого акта; `confidence=medium`.
- `run_all()` — попарний обхід документів + лінки; кандидати **не зберігаються**, `review_status="Не підтверджено"`.
- Не реалізовано (в UI підписані як «(скоро)»): `SPECIAL_VS_GENERAL`, `CODE_DUPLICATION`, `UNCONSTITUTIONAL`, `EU_MISMATCH`.

### 4.4 Індекс уваги (`risk.py`; формула готова, не підключена; UI-словник — «індекс уваги», не «юридичний ризик»)
```
score = 30·санкція + 15·розмір_штрафу + 15·наближення_строку
      + 10·зміна_≤90дн + 10·неоднозначність + 10·підтверджений_конфлікт
      + 5·тимчасова_норма + 5·ghost_norm       (0..100)
level: ≤33 low · ≤66 mid · інакше high
```
Евристики: «штраф» → 0.6; «позбавлення/кримінальн» → 1.0; «протягом N днів» → 0.5; слова-невизначеності («за потреби, тощо, негайно») ×0.2 (cap 1.0); «воєнний стан/тимчасово» → 1.0; ревізія за 90 днів → 1.0.

### 4.5 Якість розбору (`GET /quality`)
`parsed_articles` (унікальні статті), `expected_articles` = max(номер), `gaps` (числа-пропуски), `excluded_articles` (номери, **виключені з чинного тексту за примітками джерела**: «Стаття/Статтю … виключено», включно з виключеними розділами — визначається з `normalized_text`, не хардкод), `empty`, `text_outside_structure_pct`; статус: `<50%` → `quarantine`, **непояснені** пропуски/порожні → `warning`, інакше `ok`.
Доказ: Конституція **158/161, `gaps_count=0`, виключено №121–123 (Розділ VII «Прокуратура»), статус `ok`**; 12 із 13 актів `ok`; єдиний `warning` — КЗпП №322-08 (пропуски №257–258 — їх немає і в офіційному тексті, тобто це чесний пропуск, а не виключення).

### 4.6 AI (RAG) — див. повні промти в §7
`SearchService.search(question, limit=10)` → перша стаття кожного хіта як контекст (`[Норма i] heading\n text[:1500]`) → провайдер (`mock|groq|openai|anthropic`) → відповідь, `key_points` (5 перших рядків), 3 цитування з **реальною перевіркою** `verify_citation()` (`verified` = підрядок у тексті норми), `confidence` = частка підтверджених цитат (без хардкоду), невідповідні → `warnings`; помилка провайдера → чесне «Сервіс недоступний» (без фолбеку в мок). Порожній контекст → «не знайдено в базі», `confidence=0.0`; mock → «Демо-відповідь», `confidence=0.0`.

---

## 5. Інтерфейс (усі 14 сторінок)

| Маршрут | Що це |
|---|---|
| `/` | → redirect `/uk` |
| `/uk` | Огляд: hero «Законодавство, яке видно наскрізь» + пошук + **3D-сцена як фон** (вуаль), 6 швидких дій, «Акти в базі» (8), «Стан даних» |
| `/uk/legislation` | Пошук: `#sq`, діапазон дат, чекбокс тестових даних, debounce 300 мс, `Знайдено: N`, `.lvl`-рядки |
| `/uk/legislation/[id]` | Картка акта, 3 вкладки: **Текст** (положення + редакції), **Аналіз** (4 плитки), **Якість розбору** (плитки, статус, пропуски №N) |
| `/uk/assistant` | AI-запит → відповідь, «Ключові тези», «Цитування з джерела» (✓/·), `confidence`, провайдер, ⚠ warnings |
| `/uk/conflicts` | Драбина 8 рівнів сили, 4 правила вибору, список знайдених колізій (9 типів, confidence, правило, пояснення) |
| `/uk/legal-map` | Селектор 20 актів → вузли/ребра (докі порожній граф — стаб API) |
| `/uk/monitoring` | Правила моніторингу: створення/список/видалення |
| `/uk/changes` | Останні акти за датою + стан джерел (справжній стрім змін — поки що сортування списку) |
| `/uk/workspace` | Приватне сховище документів (список; завантаження — беклог) |
| `/uk/bookmarks` | Закладки користувача (посилання, нотатка, видалення) |
| `/uk/reports` | 4 KPI (акти/редакції/статті/зв'язки); експорт — беклог |
| `/uk/contracts` | Договори: список + деталі (`file_metadata`); видалення — soft delete |
| `/uk/settings` | Вхід/реєстрація/вихід (JWT у localStorage), мова/сповіщення |
| `/uk/admin` | **Звіт імпорту**: тривалість, знайдено/додано/оновлено/помилки, «Не імпортовано» URL+причина, попередження, попередні запуски, стан джерел, кнопка запуску |
| `/three` | Демо сцени на весь екран |

**Оболонка**: сайдбар (8 + «Джерела та тема»: зовнішнє «Верховна Рада» → zakon.rada.gov.ua, «☀ Світла тема / 🌙 Нічна тема»); `NAV_ALL` = 14; Ctrl+K-палітра (Enter → перший збіг, зовнішні URL — новий таб); шапка: бургер (≤860px), кнопка пошуку + `Ctrl K`, чип «Актів у БД»; футер: дисклеймер + атрибуція «Дані: Верховна Рада України, zakon.rada.gov.ua».

**Стани**: 13 `loading.tsx` (skeleton), однакові `error.tsx` (reset), `not-found.tsx`; порожні стани `EmptyState`; toast (3800 мс, поки не використовується).

**Тема**: `lib/theme.ts` — `readTheme()/applyTheme()` → localStorage `ai-ugoda-theme` + клас `.theme-light` + `CustomEvent("ai-ugoda-theme-change")`; inline-скрипт у `head` прибирає блиск при завантаженні; споживачі: шелл-кнопка, 3D-сцена (день/ніч).

**Шрифти**: Playfair Display (заголовки/бренд), Inter (UI), Source Serif 4 (`.law`, `.lead`), JetBrains Mono (`kbd`, `.meta`).

---

## 6. Анімації (повний перелік)

**Логотип (`logo.css`)**: `lgdraw` — обведення штрихом 1.2s; `lgpop` — «поп» терезів (0.6s, затримки 1/1.2/1.35s); `lgset` — хитання коромисла 2.4s (−9°→6°→…→0°); `lgspin` — печатка 360°/60s.

**Splash**: `splashout 0.45s 1.8s forwards` + розмонтування на 2300 мс; вимкнений при `navigator.webdriver`.

**globals.css**: `drift` (фонові `blob` 60/78s), `in` (вʼїзд `.view` 0.5s, `.pal` 0.25s), `shimmer` (skeleton 1.4s); переходи: `.nav` 0.2s, `.btn` hover `translateY(-2px)` 0.2s, **`.btn.p::after` блиск** (білий градієнт −60%→120% 0.7s), `.lvl` 0.25s, `.toast` 0.35s, мобільний сайдбар `transform 0.35s`, `.field:focus`, focus-visible золоті 2px, tabs `transition-colors`.

**Тема**: кольорові змінні міняються без переходу; анімується лише 3D-день/ніч (lerp ~1.6).

**Сцена (кожен кадр)**: камера-лерп `k=min(1, dt·4)` + авто-оберт після 4с простою; день/ніч-лерпи (небо/туман/світло/вода); мерехтіння вікон (`sin`-добуток ±15%), пульс ліхтарів, хвилі річки (18), маятник терезів `0.14·sin(0.9t)`, 8 машин (зʼявлення/згасання на краях), 16 перехожих (кроки `sin(7v)`, підскок, вхід у двері → спалах), 30 світлячків, 180 зірок, ветер у деревах, hover/selected масштаб хотспотів 1.03.

**Модалки**: `.modal` none→flex, `.pal` `in .25s`, бекдроп-клік — закрити.

**`prefers-reduced-motion`**: 3 рівні (globals ×2, logo, сцена) — усі переходи/анімації вимикаються, лерпи ×30.

**framer-motion**: у `dependencies`, але **0 використань** (претензія — див. STATUS §3).

**Tailwind-кейфрейми** (наявні, рідко використовуються): `fade-in`, `slide-up`, `pulse-soft`, `logo-draw/pop/stamp`, `shimmer`.

---

## 7. AI-промти (повні тексти, `apps/api/app/services/ai_service.py`)

**System (однаковий для groq/openai/anthropic):**
```
Ви — юридичний асистент для законодавства України. Відповідайте лише на основі
наданого контексту. Кожне твердження повинне мати посилання на статтю та акт.
Якщо інформації немає в контексті, кажіть «не знайдено в базі». Не вигадуйте закони.
```

**User (усі провайдери):**
```
Контекст (положення законодавства):
{context}

Питання: {question}
```

**Сам контекст** (`_build_context`): `[Норма {i}] {heading}\n{text[:1500]}\n`, перші 10 хітів (для підсумку — перші 10 редакцій).

**Промпт підсумку акта** (`summarize_act`, передається як `question`):
```
Зведіть короткий опис цього законодавчого акта: {doc.title}

Контекст: {context}
```

**Конфігурація провайдерів:**

| Провайдер | Endpoint | Модель (default) | Параметри |
|---|---|---|---|
| `groq` | `api.groq.com/openai/v1/chat/completions` | `llama-3.1-8b-instant` | `temperature 0.3`, `max_tokens 1000` |
| `openai` | `api.openai.com/v1/chat/completions` | `gpt-4o-mini` | `temperature 0.3`, `max_tokens 1000` |
| `anthropic` | `api.anthropic.com/v1/messages` | `claude-3-haiku-20240307` | `temperature 0.3`, `max_tokens 1000`, `anthropic-version: 2023-06-01` |
| `mock` (зараз) | — | — | без викликів; `confidence=0.0`, `verified=false`, явне попередження «Демо-відповідь…», quote 100 символів |

**Верифікація цитувань**: `ask()` викликає `verify_citation()` для кожної цитати; `verified` = підрядок у тексті норми; `confidence` = **частка підтверджених цитат** (0.0..1.0, без хардкоду); невідповідність → `warnings`. Помилка провайдера → чесне «Сервіс відповідей тимчасово недоступний» без фолбеку в мок. UI показує «впевненість не обчислювалася», якщо `confidence=0` або `provider=mock`, і «✓ підтверджено текстом норми» лише для `verified=true`.

**Загальна риторика, зафіксована в UI**: «не вигадуємо закон», кожне твердження → стаття + акт + дата, «не знайдено в базі» — прийнятна відповідь.

---

## 8. Безпека

- **Залежності (11.11.2026)**: `pip-audit` 0, `npm audit` 0, `bandit` 0. Заміни: `python-jose`→`PyJWT 2.15` (CVE-2026-85394 без фіксу), `lxml 6.1.0`, `python-multipart 0.0.31`, `certifi 2026.10.23`, `pytest 9.0.3`, `next 16.4.6` (критичні CVE закриті).
- **JWT**: HS256; у `deps.py`/`auth.py` — явний `algorithms=[...]` (огородження від алгоритм-плутанини).
- **Стартовий гард**: в `production` — `RuntimeError`, якщо `SECRET_KEY=="dev-secret-change-me"` або `AUTH_DISABLED`.
- **Rate limit**: 120/хв на IP, Redis ZSET, фолбек in-memory, винятки `/health,/docs...`.
- **Headers**: nosniff, DENY, Referrer-Policy, CSP (`frame-ancestors 'none'`), CORS з `CORS_ORIGINS`.
- **Джерела**: білий список хостів, HTTPS only, двостадійна валідація, `AuditLog(action="source_not_allowed")`, rate 1 req/s, UA з контактом.
- **Секрети**: `.env` у `.gitignore`; grep-патерни ключів — 0.
- **Дані договорів**: не в спільному індексі, soft delete, `retention_policy`, `CONTRACT_RETENTION_DAYS=90`.

## 9. Юридичне рев'ю (очікує юриста)

1. **Ієрархія норм** (`conflict_engine.py`): «вища сила перемагає нижчу»; спеціальна > загальна; новіша > старіша; правила GHOST_NORM/EXPIRING.
2. **Індекс уваги** (`risk.py`): ваги 30/15/15/10/10/10/5/5 — робочі значення, остаточно затверджує юрист; у словах UI — «індекс уваги», не «юридичний ризик».
3. **RAG/цитування** (`ai_service.py`): без вигадок; стаття+акт+дата; «не знайдено» — ок; `verify_citation()` коректний (підключити).
4. **8 рівнів сили**: 100/90/80/70/60/50/40/30 — ст. 8, 106, 116 КУ; 5, 16, 22 КУпАП.
5. **Персдані**: поза спільним індексом; soft delete; 90 днів зберігання; Закон «Про захист персональних даних».

## 10. Тести й CI

- **pytest (30+2)**: `test_auth` (JWT/bcrypt), `test_s3_fixtures` (4 реальні фікстури: статті, `{nreg}/article/N`, checksum, JSON-каталог), `test_s3_import`, `test_import_service`, `test_conflict_engine`, `test_fts_ukrainian`, `test_sql_injection`, `test_load` (2 skipped без PG).
- **Playwright (19)**: home (canvas, один бренд, шрифти Playfair/Inter, лічильник, 0 console errors), search («Знайдено: 13», унікальні href, 2 date), smoke 14 сторінок 200, S3 документ (Конституція ≥150 статей), S3.6 якість, auth (реєстрація→токен→200→вихід); скриншоти: `s1-home/search`, `s3-document`, `s3-quality`.
- **CI** (`ci.yml`): jobs `web` (npm ci, tsc, playwright install) та `api` (pip install, ruff, `alembic upgrade head`, pytest) з PG16 pgvector-сервісом.
- **Фікстури**: `tests/fixtures/` — `constitution_254k.frame.html` (402 531 B), `ck_435-15.frame.html` (2 788 405 B), `laws_list.json` (2 058 B) — з офіційних хостів.
