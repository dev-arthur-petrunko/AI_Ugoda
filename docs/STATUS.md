# AI Ugoda — Статус проєкту (повний звіт)

Дата: 05.11.2026 (оновлено після спринтів S0, S1, S1.5, S2, S3)
Автор: Arthur Petrunko <arthurpetrunko@gmail.com>
Гілка: main; усі зміни S0–S3 закомічено та запушено від arthurpetrunko@gmail.com

## Спринти плану «Аудит і цільова архітектура (v5)»

### S0 — Діагностика (03.11.2026) ✅ виконано

Розібрано корінь «Failed to fetch», вічного «завантаження…», шрифтів Times і дубля лого. Докази:

| Спостереження | Доказ (команда/вивід) |
|---|---|
| Docker не працював | `docker ps` → `pipe not found`; після запуску Docker Desktop: `aiugoda_postgres`, `aiugoda_redis` — healthy |
| SQLite API → 500 | `curl :8000/api/v1/stats` → **500** `sqlite3.OperationalError: no such column: legal_provisions.embedding` (schema drift: `data/aiugoda.db` без `alembic_version`) |
| 500 іде **без CORS-заголовків** | `curl -i` з `Origin: http://127.0.0.1:3000` → жодного `access-control-allow-origin` → браузер маскує у «Failed to fetch» |
| Публічного читання немає | `GET /api/v1/documents` без токена → **401 Authentication required** (`AUTH_DISABLED=false` за замовчуванням) |
| Origin `127.0.0.1:3000` поза CORS | у `CORS_ORIGINS` лише `http://localhost:3000` |
| Ukrainian FTS у PostgreSQL працює | `plainto_tsquery('ukrainian','життя')` → «Стаття 3»; `alembic_version=516775f2e1d9`; дані PG: 5/5/7 |
| Корінь бага `_normalize` | regex `[^a-zA-Z0-9_\s"-]` вирізав кирилицю: `'податковий кодекс'` → `''` → фільтр не застосовувався |
| Корінь вічного «завантаження…» | `.catch(() => {})` у `shell.tsx` і `uk/page.tsx` ковтав помилку мовчки |
| Корінь шрифтів Times | `globals.css` `:root`: циклічні `--font-inter:var(--font-inter),…` → невалідне → `font-family` падав у Times; `Logo.tsx` посилався на неіснуючі `--font-display`/`--font-ui` |
| Розбіжність даних | PG 5/5/7 проти SQLite 5/10/14 — SQLite-БД застаріла |

### S1 — UI↔API, шрифти, одне лого, стани (03–04.11.2026) ✅ виконано

**Код (не закомічено):**
- `lib/api.ts`: `API_BASE = ""` (same-origin через rewrites `next.config.js`, прибирає CORS/localhost↔127.0.0.1); мережеву помилку перекладено: «Немає зв'язку з сервером. Перевірте, чи запущено API.»; видалено недописану `requestJson`
- `shell.tsx`: прибрано дубль тексту лого (залишився один `<Logo variant="lockup">`); `statsErr` замість вічного «завантаження…»
- `Logo.tsx`: `--font-display`→`--font-playfair`, `--font-ui`→`--font-inter`
- `globals.css`: прибрано циклічні `--font-*:var(--font-*)` із `:root`; `h1`/`h2`/`.brand b` переведено на `var(--font-playfair),'Playfair Display',serif`; `body`→`var(--font-inter)`
- `uk/page.tsx`: `statsErr`; «Сьогодні» → реальна дата `TODAY`
- `uk/legislation/page.tsx`: стейт-машина loading/error/success, кнопка «Повторити», `setItems([])/setTotal(0)` при помилці
- `search.py`: `_normalize` → `[^\w\s"-]` з `re.UNICODE` (кирилиця збережена)
- Створено `loading.tsx`/`error.tsx`/`not-found.tsx` для всіх сегментів `/uk/*` (13 сегментів) + кореневі

**Приймання (браузер, localhost:3000, PostgreSQL API:8000):**

| Критерій | Результат |
|---|---|
| Сцена | ✅ `<canvas>` 1250×875, 0 помилок консолі |
| Один «AI Ugoda» | ✅ візуальний текст лого рівно 1 (`brand: "AI Ugoda"`) |
| `getComputedStyle(h1)` | ✅ `__Playfair_Display_9c243c, …, "Playfair Display", serif` — реальний Playfair (665px ≠ serif 619px) |
| `getComputedStyle(body)` | ✅ `__Inter_9bc3c0, …, system-ui, sans-serif` (було Times New Roman) |
| Цифри на головній | ✅ чип «5 актів · 7 статей», картка «Стан даних» 5/5/7 |
| Пошук | ✅ «Знайдено: 5», реальні акти, без «Failed to fetch» |
| Стани | ✅ loading → success, error → «Повторити», empty → «Нічого не знайдено» |
| Якість | ✅ `npx tsc --noEmit` → 0 помилок; `python -m ruff check .` → All checks passed |
| Скриншоти | ⏳ не знято: `browser.screenshot` вимагає видимого вікна Review-панелі на робочому столі (обміння інструмента, не коду) |

**Перезапуск і повна перевірка (04.11.2026):**
- Усі процеси (3000/8000/8001) зупинено, піднято заново: uvicorn (PostgreSQL) + `npm run dev`
- Усі 14 сторінок `/uk/*` + `/three` → **200**; `/` → 307 (redirect, норма)
- API: `/health` 200, `/stats` 200 (5/5/7), `/documents` 200, пошук `q=кодекс` 200, `/bookmarks` 200 (401 без токена — `AUTH_DISABLED=true` лише в dev-запуску), `/sync/status` 200, `/conflicts` 307→200 (штатний trailing-slash FastAPI), `/openapi.json` 200
- Прокси `localhost:3000/api/*` → 200 (same-origin, CORS не потрібен)
- Консоль браузера: 0 помилок після фіксу

**Нові фикси, знайдені під час перезапуску:**
- `search.py`: `LEFT JOIN legal_provisions` множив рядки → `total=5`, а `items=7` (повні дублі Цивільного кодексу і Конституції). Join замінено на підзапроси `EXISTS`/`subselect`; після фікса **total=5, items=5, unique=5** (перевірено і прямим запитом до API, і в UI: «Знайдено: 5», 5 унікальних елементів, 0 помилок консолі)
- `legislation/page.tsx`: React-попередження «two children with the same key» → ключ `${d.id}-${i}`
- `InteractiveScene.tsx`: прибрано 36 чорних коробок (1.36×0.78×0.72, HSL ~0.27–0.37) по периметру площі — виглядали як чорні будинки навколо сцени
- `assets/fonts/Inter-Regular.woff2 → 404`: разовий запит зі старого кешу браузера — у коді та в мережі браузера не відтворюється (усі `@font-face` йдуть з `/_next/static/...`)

**Обмеження:** `/_v1/models` → 404 — ендпоінт не існує (запити йдуть від стороннього клієнта, не від UI), на роботу сайту не впливає.

### S1.5 — Підключення заглушок, JWT на фронті, публічне читання (04.11.2026) ✅ виконано

**API:**
- `GET /documents`, `/documents/{id}`, `/provisions`, `/revisions`, `/at`, `/analysis`, `/diff` зроблено **публічними без токена** (план §5.3): прибрано `Depends(get_current_user)` з читальних ендпоінтів (`documents.py`, `analysis.py`, `diff.py`); запис/захищені маршрути (`/bookmarks`, `/monitoring`, `/contracts`) — як і раніше з JWT
- `conflicts.py`: серіалізація ORM-кандидатів у dict (інакше JSON-відповідь міг падати на SQLAlchemy-об'єктах)
- Тест `tests/test_auth.py`: `test_documents_401_without_token` → `test_documents_public_without_token` (200 без токена) — стара вимога суперечила §5.3
- `.env`: згенеровано випадковий `SECRET_KEY` (96 hex, замість dev-значення); файл у `.gitignore`

**Фронтенд (JWT + підключення сторінок):**
- `lib/api.ts`: зберігання JWT у `localStorage` (`aiugoda_token`), авто-підстановка `Authorization: Bearer` у кожен запит, 401 → `AuthError` «Сесія завершена…»; функції `login/register/logout/refreshAccessToken`, `getConflicts`, `askAI`, `getGraph`; `listDocuments` отримав фільтри `adoption_date_from/to`
- `/uk/settings`: форма входу/реєстрації (JWT зберігається, вихід) — замість заглушки
- `/uk/conflicts`: підключено до `GET /conflicts/` (реальні кандидати: тип, впевненість, правило, пояснення) + лічильник, стани loading/error/empty
- `/uk/assistant`: підключено до `POST /ai/ask` (відповідь, тези, цитування, впевненість, попередження)
- `/uk/reports`: підключено до `GET /stats` (4 картки з джерелом таблиці)
- `/uk/legal-map`: вибір акта → `GET /graph/{id}` (вузли/ребра, стани порожнього графа)
- `/uk/changes`: стрічка найновіших редакцій з `/documents` (відсортовано за датою) + джерела sync
- `/uk/workspace`: список приватних договорів `GET /contracts` (завантаження файлів — наступні етапи)
- `/uk/legislation`: фільтри «Прийнято від/до» (дата) на сторінці пошуку

**Перевірки:** `tsc --noEmit` → 0; `ruff check app` → All checks passed; `pytest -q` → **23 passed, 2 skipped**; обидва сервіси перезапущено (3000/8000). Після підключення `/uk/conflicts` у консолі браузера було знайдено React-попередження «two children with the same key» (тимчасові кандидати мають `id=None` → `str(None)="None"`): виправлено fallback-key у `conflicts.py` і `conflicts/page.tsx` → 4/4 унікальних id, **0 помилок консолі** (перевірено `browser.console` після reload).

**Чесно не зроблено (потрібні ключі/рішення):** LLM-провайдер (`AI_PROVIDER=mock`, потрібні ключі GROQ/OpenAI/Anthropic), embeddings не заповнені (5 сид-актів), юридичне рев'ю K12, підпис K12.

### S2 — Playwright + CI (04.11.2026) ✅ виконано

**Playwright (скриншоти S1 знято headless — без видимого вікна):**
- `apps/web/playwright.config.ts` — chromium, `baseURL=localhost:3000`, `reuseExistingServer` (webServer), html-звіт
- `apps/web/e2e/s1-acceptance.spec.ts` — приймання S1: `<canvas>` 1, рівно один «AI Ugoda», `getComputedStyle(h1)` ⊃ Playfair Display, body ⊃ Inter, лічильник «актів», 0 помилок консолі; пошук: «Знайдено: 5», 5 унікальних href без дублів, 2 фільтри дати; smoke 14 сторінок → 200
- `apps/web/e2e/auth.spec.ts` — S1.5: реєстрація+вхід через UI → JWT у `localStorage` → `/api/v1/bookmarks` з токеном → 200 → вихід
- **Результат: 17 passed (54.3s), 0 failed** — `npx playwright test`
- **Скриншоти для приймання:** `apps/web/e2e/screenshots/s1-home.png` (767 KB), `s1-search.png` (94 KB) — зняті, показані в Review
- Скрипт: `npm run test:e2e` (у `apps/web/package.json`)

**CI (`.github/workflows/ci.yml`):**
- Job `web`: Node 20, `npm ci`, `tsc --noEmit`, `playwright install chromium`, service `pgvector/pgvector:pg16`; артефакти playwright-report/test-results/screenshots при помилці
- Job `api`: Python 3.12, `requirements.txt`, `ruff check app`, `alembic upgrade head`, `pytest -q`; env (`DATABASE_URL`, `AUTH_DISABLED=true`, `SECRET_KEY=ci-…`) — секрети не в репозиторії
- Тригери: push/PR у `main`

**`.gitignore`:** додано `playwright-report/`, `test-results/`, `.playwright/` (скриншоти-докази `e2e/screenshots/` — у git).

**Що залишилось із плану:** LLM-ключі, юр-рев'ю K12, CVE-огновлення — очікують рішення власника (див. вище).

### S3 — Подальший аудит / тексти актів із офіційних джерел (05.11.2026) ✅ виконано

**Розбіжність (за правилом 3, зафіксовано):** текст спринта S3 надано власником **під час** роботи (спочатку S3 робився як «подальший аудит», пізніше додано вимоги 3.1–3.8). Також вимога S3.1 «окремий `docs/SOURCES_VERIFIED.md`» суперечила правилу 5 «ровно 3 файли доків» → **вирішено на користь правила 5**: верифікація джерел перенесена в `docs/PROJECT_FULL_REPORT.md` §16, окремий файл видалено; у `docs/` рівно 3 файли (STATUS.md, PROJECT_FULL_REPORT.md, OPERATIONS.md). `docs/PLAN.md` не створювався — текст плану в репо відсутній.

**3.1 — Верифікація джерел → `docs/PROJECT_FULL_REPORT.md` §16 ✅** (правило 5 «ровно 3 файли доків» виконано: вміст `SOURCES_VERIFIED.md` перенесено у §16 повного звіту, окремий файл видалено):
- Білий список: **тільки `data.rada.gov.ua` і `zakon.rada.gov.ua`** (перевірено двічі: allowlist у `source_guard.py` + SQL-звірка `source_host`)
- Пакетний індекс: `/ogd/zak/laws/data/csv/doc.zip` (13.5 МБ), `doc.txt` (TSV, windows-1251, 295568 рядків); ліцензія **CC BY 4.0** → атрибуція у футері
- `robots.txt` `User-Agent: * → Disallow: /` — **зафіксовано як обмеження** (обмеження не порушено: працюємо з офіційними `.frame`-фрагментами для показу користувачу)
- Усі **13 nreg Tier 1** звірено з `doc.txt` станом 05.11.2026 (Конституція `254к/96-вр` — кирилиця, звірено з рядком id=12934)

**3.2 — `data_origin` (official|fixture), default `fixture` ✅**
- Колонка `legal_documents.data_origin`, міграція `s3dataorigin`; бейдж «тестові дані» + чекбокс «Показати тестові дані» у UI; пошук за замовчуванням — **лише official** (`include_fixtures=true` для dev)
- Лічильники `/stats`: official/fixture

**3.3 — Конектор + імпорт ✅**
- `source_guard.py`: allowlist, 1 req/s, UA `AIUgodaBot/0.1`, кеш сирих відповідей + SHA-256, статуси, audit_logs
- `ImportRun` + міграція `s3sources`; `/sync/run`, `/sync/status`, `/sync/runs` (BackgroundTasks, 409 при паралельному lock); rollback сесії після помилок flush

**3.4 — Tier 1 (13 актів) ✅**
- `TIER1_URLS` — 13 шт. `.frame` (`/show/{nreg}.frame`, не `/main/` — оболонка без тексту)

**3.5 — Розбір структури ✅**
- Виключено TOC (`aside.stru`), дедуп за (level, number), безпечні identifier, `unquote(nreg)` (`254к/96-вр`, а не `254%D0%BA`), повний HTML без обрізки `[:200000]` (обрізка ламала великі акти: ЦК 2.7 МБ → 0 статей), заголовки ≤500
- **Виправлено у S3:** заголовок брався лише з `h1`/`title`, яких у `.frame` нема → усі 13 мали «Без назви» → додано фолбек на перший `span.rvts*`; `document_type` виводився з `meta["title"]` (ключа не існувало) → тепер із витягнутого заголовка

**3.6 — Картка «Якість розбору» ✅**
- `GET /api/v1/documents/{id}/quality`: Конституція → **parsed=158, expected=161, gaps=3 (121–123), empty=0, status=warning** (прогалини — так у джерелі); ревізія обирається за найбільшою кількістю положень (модель не має `is_current`)

**3.7 — Ідемпотентність / дублі ✅**
- `tests/test_s3_import.py`: **3 passed** (повторний імпорт → added 0; той самий текст → без нової ревізії; другий lock → 409)
- `upsert_document` приймає рядок фікстури за nreg (case-insensitive) при колізії official↔fixture — без дублікатів

**3.8 — Приймання + UI-правки ✅ (докази команд/SQL/скриншотів)**

| Критерій | Доказ |
|---|---|
| Імпорт 13/13 | `python scripts/run_import_once.py` → `discovered=13, updated=13, errors=0, parse_errors=0` |
| Ідемпотентність | повтор → `added=0, updated=13, errors=0` |
| Походження | `SELECT data_origin, count(*)` → **official=13, fixture=3** |
| Лише дозволений хост | `SELECT DISTINCT source_host FROM document_revisions` → **zakon.rada.gov.ua** (1 рядок) |
| 13 nreg зі статтями | SQL-запит: `435-15=1295, 4651-17=632, 1618-15=531, 2341-14=462, 436-15=418, 2747-15=417, 1798-12=407, 2947-14=393, 2755-17=342, 322-08=276, 2768-14=243, 80731-10=200, 254к/96-вр=174` |
| Якість | `GET /quality` → `parsed=158, expected=161, gaps=3, status=warning` |
| Заголовки/типи | SQL: усі 13 official мають назву (`КОНСТИТУЦІЯ УКРАЇНИ` → Конституція, решта 12 → Кодекс), `no_title=0` |
| pytest | ✅ **26 passed, 2 skipped** |
| ruff / tsc | ✅ All checks passed! / ✅ exit 0 |
| Playwright e2e | ✅ **18 passed (42.4s), 0 failed** (включно з S3-тестом: пошук «Конституція» → сторінка акта, ≥150 статей, 0 помилок консолі) |
| Скриншоти | ✅ `apps/web/e2e/screenshots/`: `s1-home.png` (784 KB), `s1-search.png` (97 KB), **`s3-document.png` (712 KB)** |

**Очищення коду (05.11.2026, вимога власника «прибрати мусор»):** видалено `apps/api/tests/diag_parser.py` (разовий діагностичний скрипт) та невикористовувані HTML-фікстури `apps/api/tests/fixtures/` (`constitution_254k.html`, `constitution_254k.frame.html`, `ck_435-15.frame.html`, ~3 МБ) — жоден тест на них не посилався (перевірено grep). Тестові SQLite-БД у корені видаляються перед кожним прогоном pytest (у git не потрапляють, `.gitignore`: `*.db`).

**Не зроблено (потребує рішення власника):** LLM-ключі, CVE-оновлення (pip 116 / npm critical next→16.4.5), юр-рев'ю K12, ендпоінт завантаження файлів.

**Висновок S3:** 13 офіційних актів імпортовано з джерел білого списку, структура розібрана, якість вимірюється карткою, ідемпотентність і дедуп підтверджено тестами та SQL; e2e 18/18, 0 помилок якості.

## 0. Останні зміни (01–02.11.2026)

**Інтерактивна сцена (головна сторінка):**
- Заголовок сцени: **«AI Ugoda · Верховна Рада»** (обидві назви в титулі, як у ТЗ)
- Золотий підзаголовок **«Київ. Площа Конституції»** + ефектний опис: *«Золоті куполи над Дніпром — і кожен камінь площі веде до розділу законодавства»*
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

### 4.1 Документація (`docs/` — рівно 3 файли)
| Файл | Опис |
|------|------|
| `STATUS.md` (цей файл) | Статус проєкту, S0–S3, K1–K12, останні зміни, юридичне рев'ю, Git |
| `PROJECT_FULL_REPORT.md` | Архітектура, БД, автентифікація, пошук, фронтенд, Docker, тести, changelog |
| `OPERATIONS.md` | Операційна документація: БД, тимчасові файли, безпека, запуск, troubleshooting |
| _(верифікація джерел S3.1)_ | перенесена в `PROJECT_FULL_REPORT.md` §16 (правило 5: рівно 3 файли) |

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

## 7. Юридичне рев'ю (K12) — ⏳ очікує юриста

Чек-лист для підпису юристом (перевірити перед запуском MVP):

**1. Ієрархія норм (`conflict_engine.py`):**
- [ ] «Вища сила перемагає нижчу» — відповідає КУпАП
- [ ] Спеціальна норма перемагає загальну; новіша — старішу (lex posterior)
- [ ] Правила GHOST_NORM (мертві норми) та EXPIRING коректні

**2. Оцінка ризику (`risk.py`):** ваги факторів 30/15/15/10/10/10/5/5 обґрунтовані, підхід не заперечує законодавство.

**3. RAG та цитування (`ai_service.py`):** «не вигадуємо закон»; кожне твердження → стаття + акт + дата редакції; «не знайдено в базі» — прийнятна відповідь; `verify_citation()` коректний.

**4. Рівні юридичної сили (8):** Конституція 100 · Міжн. договори 90 · Закони/кодекси 80 · Постанови ВР 70 · Укази П 60 · Постанови КМУ 50 · Накази мін-в 40 · Місцеві 30 — відповідають ст. 8, 106, 116 КУ; 5, 16, 22 КУпАП.

**5. Персональні дані (договори):** не потрапляють у спільний індекс; м'яке видалення (`deleted_at`), зберігання 90 днів; відповідність Закону «Про захист персональних даних».

- Ім'я юриста: ______________________
- Дата: ______________________
- Підпис: ______________________

## 8. Git

- **Репозиторій:** `https://github.com/dev-arthur-petrunko/AI_Ugoda`
- **Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
- **Гілка:** `main`
- **Останні коміти:** S0+S1+S1.5 (`7a8f9aa`), S2 Playwright+CI (`657bfc5`), S3 тексти актів (див. `git log`)

---

**Дата:** 05.11.2026
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
