# AI Ugoda — Аналіз сайту (фронтенд + бекенд)

**Дата аналізу:** 26.10.2026
**Робоча директорія:** `C:\Users\Arthur\Desktop\AI Ugoda`
**Гілка:** `main` (коміт `da73f6d`, запушений у `origin/main`)
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>

---

## 1. Загальний огляд

AI Ugoda — юридична інтелектуальна платформа: каталог законодавства України з пошуком, переглядом акту на дату, структурою статей, редакціями, колізіями, аналізом договорів, AI-юристом.

- **Frontend:** Next.js 14.2.15 (App Router), TypeScript, Tailwind, Framer Motion, Lucide.
- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic + SQLite (dev) / PostgreSQL (продакшн через Docker).
- **Тести:** pytest 11 passed / 2 skipped (FTS потребує PostgreSQL); ruff 0 помилок.
- **Архітектура UI:** app-shell з фіксованим сайдбаром і внутрішнім скролом.

---

## 2. Стан запуску (перевірено)

| Сервіс | URL | Статус |
|--------|-----|--------|
| Backend (FastAPI/uvicorn) | http://localhost:8000 | `/health` → 200 |
| `/api/v1/stats` | — | 401 без токена (потрібен `Authorization: Bearer dev-secret-change-me`) |
| `/api/v1/documents` | — | 401 без токена |
| `/api/v1/documents/05ed62e8-...` | — | 401 без токена |
| `/api/v1/documents/nonexistent-id` | — | 404 (з токеном, в коді) |
| `/api/v1/sync/run` | — | 403 (без прав адміна) / 401 (без токена) |

**Пошук (базова лінія, SQLite in-memory, 50 документів):**
- `q='Конституція'` → total=50, 6.24 ms
- `q='кодекс'` → total=50, 0.88 ms
- `q='Стаття 1'` → total=14, 1.16 ms
- `q='неіснуючеслово12345'` → total=0, 0.41 ms

Пошук на SQLite виконується через `LIKE` (search.py:144). На PostgreSQL — `plainto_tsquery('ukrainian', ...)` (не перевірено без Docker/PostgreSQL).

---

## 3. Сторінки фронтенду (`apps/web/src/app/uk/`)

| Маршрут | Файл | Стан даних |
|---|---|---|
| `/uk` | `page.tsx` | ✅ Підключено `/api/v1/stats` |
| `/uk/legislation` | `legislation/page.tsx` | ✅ Підключено `/api/v1/documents?q=` |
| `/uk/legislation/[documentId]` | `legislation/[documentId]/page.tsx` | ✅ Підключено (документ, статті, редакції) |
| `/uk/admin` | `admin/page.tsx` | ✅ Підключено (`/sync/status`, `/sync/run`) |
| `/uk/assistant` | `assistant/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/changes` | `changes/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/contracts` | `contracts/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/conflicts` | `conflicts/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/legal-map` | `legal-map/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/monitoring` | `monitoring/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/reports` | `reports/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/settings` | `settings/page.tsx` | ⚠️ Статичний placeholder |
| `/uk/workspace` | `workspace/page.tsx` | ⚠️ Статичний placeholder |

---

## 4. API-ендпоінти бекенду (`/api/v1`)

**Health:** `GET /health`  
**Stats:** `GET /stats` → `{documents, revisions, provisions, links}`  
**Sync:** `GET /sync/status`, `POST /sync/run`

**Documents (`/documents`):**
- `GET /` — список/пошук (`q`, фільтри: тип, статус, орган, дати, рівень сили, `only_current`, пагінація)
- `GET /suggestions?q=` — автозаповнення
- `GET /search/by-provision?provision_ref=` — пошук за статтею
- `GET /{document_id}` — документ
- `GET /{document_id}/provisions` — структура акту (статті)
- `GET /{document_id}/revisions` — редакції
- `GET /{document_id}/at?date=` — акту на дату

**Автентифікація:** `get_current_user` — анонімний доступ лише якщо `AUTH_DISABLED=true` і `APP_ENV=development` (AND, не OR), анонімний користувач без прав адміна (`is_superuser: False`). Інакше 401.

---

## 5. Компоненти та UI-система

- `components/reference/shell.tsx` — app-shell: сайдбар, топбар, глобальний пошук (Ctrl+K), модалка навігації, toast, чіп зі статистикою БД.
- `components/brand/Logo.tsx` — знак «Терези рівноваги» (variants: `mark`, `lockup`, `seal`), розмір задається явно, анімація коливання балки.
- `components/brand/Splash.tsx` — заставка (SessionStorage, ≤ 2.2 с, пропускається кліком).
- `components/ui/loader.tsx` — екран завантаження з логотипом.
- `lib/api.ts` — типізований клієнт (всі вищезазначені ендпоінти).

**Стилі (`styles/globals.css`):** дві шкали змінних (`--gold`, `--bg` тощо), glassmorphism, анімації `draw/pop/in`. App-shell: `.app{grid-template-columns:272px 1fr; height:100%}`, `.main{flex column; height:100%; min-height:0}`, `.view{flex:1; overflow:auto; min-height:0}`.

---

## 6. Виправлені проблеми (поточний цикл)

1. **Авторизація (A4):** `AUTH_DISABLED OR APP_ENV=development` → `AUTH_DISABLED AND APP_ENV=development`; анонімний користувач тепер без прав адміна; `AUTH_DISABLED=False` за замовчуванням.
2. **Мертвий код:** видалено невиконуваний блок у `import_service.py:upsert_force_level`.
3. **Тести:** додано `tests/test_auth.py` (401 без токена) і `tests/test_import_service.py` (тест N статей → N у БД).

---

## 7. Залишкові проблеми / борг (за ТЗ)

| # | Проблема | Файл/зона | Пріоритет |
|---|----------|-----------|-----------|
| 1 | 9 сторінок-плейсхолдерів без реальних даних | `uk/{assistant,changes,contracts,conflicts,legal-map,monitoring,reports,settings,workspace}` | Середній |
| 2 | Дашборд частково статичний | `uk/page.tsx` | Середній |
| 3 | Немає реального імпорту з zakon.rada.gov.ua | `app/services/connector.py` | Середній |
| 4 | Дубль CSS-токенів дизайну | `apps/web/src/styles/globals.css` | Низький |
| 5 | Оновлення залежностей (Next.js 14 → 16, CVE в Python-пакетах) | `package.json`, `requirements.txt` | Високий (Етап 4) |
| 6 | FTS українською не перевірено без PostgreSQL | `docker/postgres/Dockerfile` | Високий (К3) |

## 8. Тести та якість

- **pytest:** 11 passed, 2 skipped (FTS-тести потребують PostgreSQL + Hunspell, Docker не запущено).
- **npm build:** ✅ (Next.js 14.2.15, без type-помилок).
- **ruff:** 0 помилок.
- **bandit:** 6 LOW (очіковано для dev).
- **pip-audit:** 98 CVE у 16 пакетах (вимагає оновлення).
- **npm audit:** 2 вразливості у `postcss`.

## 9. Запуск локально

```powershell
# Backend
cd apps/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Тести
cd ..
python -m pytest -q

# Frontend ( окрема консоль)
cd apps/web
npm run dev   # http://localhost:3000
```

## 10. Файли, змінені в поточному циклі (К1)

- `apps/api/app/api/deps.py` — авторизація `AND` замість `OR`, анонімний без адмін-прав.
- `apps/api/app/core/config.py` — `AUTH_DISABLED=False` за замовчуванням.
- `apps/api/app/services/import_service.py` — видалено мертвий код.
- `tests/test_auth.py` — новий тест 401 без токена.
- `tests/test_import_service.py` — додано тест ідемпотентності N статей.
- `docs/CLEANUP_REPORT.md` — оновлено.
- `docs/AUDIT_2026-10-26.md` — новий звіт аудиту з сировими виводами.
- `docs/PROJECT_DOCUMENTATION.md` — всесвідомлюючий документ (цей цикл).

---

**Висновок:** сайт працює, бекенд відповідає, авторизація виправлена, тести проходять. Основний борг — оновлення залежностей, PostgreSQL/FTS, 9 плейсхолдер-сторінок, JWT/Rate-limiting у продакшені.


