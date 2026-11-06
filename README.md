# AI Ugoda — navigator and risk detector over Ukrainian legislation

Navigation and risk detection over the legislation of Ukraine. From the official text to practical analysis.

> **Core project rule:** never invent a law. Every claim = reference to an act + article + revision date. Source not found — we write "not found in the database".

## English

**Sprint status: S0–S3 completed (see `docs/STATUS.md`).**

- **Sprint S0 (diagnosis):** audit of UI↔API wiring, identified main gaps.
- **Sprint S1:** same-origin API (`API_BASE = ""` via Next.js rewrites), fonts, single "scales of justice" logo, loading/empty/error states, search deduplication.
- **Sprint S1.5:** public read access without JWT (plan §5.3), JWT auth on the frontend with a login form inside `/uk/settings`, 7 placeholders connected to real API, fallback document id for conflicts.
- **Sprint S2 (04.11.2026):** Playwright e2e — **17 passed / 0 failed**, GitHub Actions CI (`.github/workflows/ci.yml`), acceptance screenshots in `apps/web/e2e/`.
- **Sprint S3 (05.11.2026):** real data sprint:
  - **3.1 Sources verified** — `data.rada.gov.ua` and `zakon.rada.gov.ua` checked with `curl.exe`; report in `docs/SOURCES_VERIFIED.md`: HTTP 200, JSON/TSV formats, `robots.txt` limitations, **CC BY 4.0** license, attribution added to the footer.
  - **3.2 Test data separated** — `seed_acts.py` → `apps/api/scripts/dev_fixtures.py`, `legal_document.data_origin` column (`official | fixture`), search defaults to official only (`include_fixtures=true` for dev), fixture badge in the UI, separate counters in `/stats`.
  - **3.3 Connector** — host whitelist (`data.rada.gov.ua`, `zakon.rada.gov.ua`, https only), polite mode (≤1 req/s, `AIUgodaBot/0.1` with contact), raw payload cache (SHA-256), source status (active/degraded/down), background import with `import_runs` log and single-run lock (409).
  - **3.4 Tier 1 act list** — all **13** nreg verified against official `doc.txt` (05.11.2026), Constitution is `254к/96-вр` (Cyrillic «к», not Latin).
  - **3.5 Structure parsing** — section → article → part → point → subpoint tree, stable addresses, SHA-256 content checksums, TOC (aside.stru) deduplication; Constitution parsed from real `.frame` HTML: **158 articles** (gaps 121–123 are absent in the official source too — verified).
  - **3.6 Quality card** — `GET /api/v1/documents/{id}/quality`: parsed/expected, numbering gaps, empty articles, status `ok/warning/quarantine`.
  - **3.7 Idempotency & duplicates** — re-import adds 0, same text under a new date does not create a new revision, concurrent second import is rejected (tests `tests/test_s3_import.py`, 3 passed).
- **Tests:** pytest **26 passed / 2 skipped**; ruff 0; tsc 0; Playwright **17 passed**.

### Security (owner decision, separate commits)

- **npm audit:** 3 issues (1 critical + 2 high) in `next` image optimization — do not expose the site publicly before upgrading to `next@16.4.5` (breaking); `next dev`/`start` must listen on localhost only.
- **pip-audit:** 116 CVE in 18 packages — re-check in a clean venv, remove unused packages, upgrade the rest.
- **bandit:** low-severity findings only; no silent `except: pass` remains in the import path.

### Quick start (Docker)

```bash
cp .env.example .env      # edit .env if needed
docker compose up --build
# Web:  http://localhost:3000
# API:  http://localhost:8000 (docs at /api/v1/docs)
```

### Repository

`https://github.com/dev-arthur-petrunko/AI_Ugoda` (push as `arthurpetrunko@gmail.com`, GitHub PAT with `repo` scope required).

See `docs/STATUS.md`, `docs/OPERATIONS.md`, `docs/SOURCES_VERIFIED.md`.

---

## Українською

**Статус спринтів: S0–S3 виконано (див. `docs/STATUS.md`).**

- **Спринт S0 (діагностика):** аудит зв'язку UI↔API, виявлено основні прогалини.
- **Спринт S1:** same-origin API (`API_BASE = ""` через Next.js rewrites), шрифти, одне лого «Терези рівноваги», стани завантаження/порожньо/помилка, дедуплікація пошуку.
- **Спринт S1.5:** публічне читання без JWT (план §5.3), JWT-авторизація на фронтенді з формою входу всередині `/uk/settings`, підключено 7 заглушок до реального API, fallback id документа в конфліктах.
- **Спринт S2 (04.11.2026):** Playwright e2e — **17 passed / 0 failed**, GitHub Actions CI (`.github/workflows/ci.yml`), скріншоти приймання в `apps/web/e2e/`.
- **Спринт S3 (05.11.2026):** спринт реальних даних:
  - **3.1 Перевірка джерел** — `data.rada.gov.ua` і `zakon.rada.gov.ua` перевірено `curl.exe`; звіт у `docs/SOURCES_VERIFIED.md`: HTTP 200, формати JSON/TSV, обмеження `robots.txt`, ліцензія **CC BY 4.0**, атрибуцію додано у футер.
  - **3.2 Відокремлення тестових даних** — `seed_acts.py` → `apps/api/scripts/dev_fixtures.py`, колонка `legal_document.data_origin` (`official | fixture`), пошук за замовчуванням лише official (`include_fixtures=true` для розробки), позначка «тестові дані» в UI, окремі лічильники у `/stats`.
  - **3.3 Коннектор** — білий список хостів (`data.rada.gov.ua`, `zakon.rada.gov.ua`, лише https), ввічливість (≤1 запит/с, `AIUgodaBot/0.1` з контактом), кеш сирих відповідей (SHA-256), статус джерела (active/degraded/down), фоновий імпорт з журналом `import_runs` і блокуванням повторного запуску (409).
  - **3.4 Список актів Tier 1** — усі **13** nreg звірені з офіційним `doc.txt` (05.11.2026), Конституція — `254к/96-вр` (кирилична «к», не латиниця).
  - **3.5 Розбір структури** — дерево розділ → стаття → частина → пункт → підпункт, стабільні адреси, контрольні суми SHA-256, дедуплікація змісту (aside.stru); Конституцію розібрано з реального HTML `.frame`: **158 статей** (прогалини 121–123 відсутні і в офіційному джерелі — звірено).
  - **3.6 Картка «Якість розбору»** — `GET /api/v1/documents/{id}/quality`: розібрано/очікується, прогалини нумерації, порожні статті, статус `ok/warning/quarantine`.
  - **3.7 Ідемпотентність і дублі** — повторний імпорт додає 0, той самий текст під іншою датою не створює нову редакцію, другий одночасний запуск відхиляється (тести `tests/test_s3_import.py`, 3 passed).
- **Тести:** pytest **26 passed / 2 skipped**; ruff 0; tsc 0; Playwright **17 passed**.

### Безпека (рішення замовника, окремі коміти)

- **npm audit:** 3 зауваження (1 critical + 2 high) в оптимізації зображень `next` — не виставляти сайт в інтернет до оновлення до `next@16.4.5` (breaking); `next dev`/`start` слухає лише localhost.
- **pip-audit:** 116 CVE у 18 пакетах — перевірити в чистому venv, прибрати невикористані пакети, решту оновити.
- **bandit:** лише low-примітки; «тихих» `except: pass` у шляху імпорту не лишилося.

### Швидкий старт (Docker)

```bash
cp .env.example .env      # відредагуйте .env за потреби
docker compose up --build
# Web:  http://localhost:3000
# API:  http://localhost:8000 (документація /api/v1/docs)
```

### Репозиторій

`https://github.com/dev-arthur-petrunko/AI_Ugoda` (пуш від `arthurpetrunko@gmail.com`, потрібен GitHub PAT з правом `repo`).

Див. `docs/STATUS.md`, `docs/OPERATIONS.md`, `docs/SOURCES_VERIFIED.md`.
