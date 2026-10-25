# AI Ugoda — Аналіз сайту (фронтенд + бекенд)

**Дата аналізу:** 25.10.2026  
**Робоча директорія:** `C:\Users\Arthur\Desktop\AI Ugoda`  
**Гілка:** `main` (коміт `8f92ffbe`)  
**Статус:** обидва сервіси запущені й відповідають (frontend :3000, backend :8000).

---

## 1. Загальний огляд

AI Ugoda — юридична інтелектуальна платформа: каталог законодавства України з пошуком, переглядом акту на дату, структурою статей, редакціями, колізіями, аналізом договорів, AI-юристом.

- **Frontend:** Next.js 14.2.15 (App Router), TypeScript, Tailwind, Framer Motion, Lucide.
- **Backend:** FastAPI + SQLAlchemy + SQLite (dev), pytest 7/7.
- **Архітектура UI:** app-shell з фіксованим сайдбаром і внутрішнім скролом (`.view`).

---

## 2. Стан запуску (перевірено)

| Сервіс | URL | Статус |
|---|---|---|
| Frontend (Next.js dev) | http://localhost:3000 | ✅ Ready in 2.5s, `/`, `/uk`, `/uk/legislation` → 200 |
| Backend (FastAPI/uvicorn) | http://localhost:8000 | ✅ `/health` → `{"status":"ok","service":"AI Ugoda","env":"development"}` |
| `/api/v1/stats` | — | ✅ `{documents:5, revisions:10, provisions:14, links:0}` |
| `/api/v1/documents` | — | ✅ 5 актів (податковий кодекс тощо) |

**Причина початкової помилки** `Cannot find module './609.js'` — зіпсований/застарілий кеш `.next` (перервана збірка). Виправлено видаленням `.next` і перезапуском `npm run dev`. `npm run build` проходить без помилок (16 маршрутів).

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

**Автентифікація:** `get_current_user` (AUTH_DISABLED прапорець через env).

---

## 5. Компоненти та UI-система

- `components/reference/shell.tsx` — app-shell: сайдбар, топбар, глобальний пошук (Ctrl+K), модалка навігації, toast, чіп зі статистикою БД.
- `components/ui/logo.tsx` — **Терези рівноваги** (scales): стійка → балка → миски → печатка (diamond) → коливання балки (0°→-9°→6°→-3.2°→1.4°→-0.5°→0°, 2.4 с, pivot у центрі). Замінено стару "U"-іконку.
- `components/layout/page-shell.tsx`, `components/ui/empty-state.tsx`, `components/ui/button.tsx`.
- `lib/api.ts` — типізований клієнт (всі вищезазначені ендпоінти).

**Стилі (`styles/globals.css`):** дві шкали змінних (`--gold`, `--bg` тощо), glassmorphism, анімації `draw/pop/in`. App-shell: `.app{grid-template-columns:272px 1fr; height:100%}`, `.main{flex column; height:100%; min-height:0}`, `.view{flex:1; overflow:auto; min-height:0}`.

---

## 6. Виправлені проблеми (цей цикл)

1. **`Cannot find module './609.js'`** — зіпсований кеш `.next`. Виправлено: `Remove-Item -Recurse .next` + перезапуск `npm run dev`.
2. **Скрол не працював** — flex-елементи `.main`/`.view` без `min-height:0` не стискались, overflow не спрацьовував. Додано `min-height:0` до обох.
3. **Логотип** — замінено стару "U" на Терези рівноваги (scales) у `logo.tsx` і `shell.tsx`.
4. **Дані не завантажувались** — огляд і пошук були статичними. Підключено `/stats` і `/documents`.
5. **Сайдбар-чіп** — тепер показує реальні лічильники БД.
---

## 7. Залишкові проблеми / борг (за ТЗ)

| # | Проблема | Файл/зона | Пріоритет |
|---|---|---|---|
| 1 | ruff: 153 помилки (вкл. 18 F821 невизначені імена) | `apps/api` | Високий |
| 2 | БД SQLite замість PostgreSQL | `app/core/database.py`, `docker-compose` | Високий |
| 3 | `AUTH_DISABLED` прапорець + відсутній rate limiting | `app/api/deps.py`, middleware | Високий |
| 4 | 9 сторінок-плейсхолдерів без реальних даних | `uk/{assistant,changes,contracts,conflicts,legal-map,monitoring,reports,settings,workspace}` | Середній |
| 5 | Дашборд частково статичний (колізії, джерела, синхронізація) | `uk/page.tsx` | Середній |
| 6 | Немає реального імпорту з rada.gov.ua / zakon.rada.gov.ua | `app/services/sync.py` | Середній |
| 7 | `docs/CLEANUP_REPORT.md` — ще не створено | — | Низький |

---

## 8. Тести та якість

- **pytest:** 7/7 passed (`tests/test_conflict_engine.py`, `test_import_service.py`, `test_sql_injection.py`).
- **npm build:** ✅ (16 маршрутів, без type-помилок).
- **ruff:** 153 помилки (не виправлено в цьому циклі).

---

## 9. Запуск локально

```bash
# Frontend
cd apps/web
Remove-Item -Recurse -Force .next   # якщо помилка ./609.js
npm run dev                          # http://localhost:3000

# Backend
cd apps/api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # http://localhost:8000
```

---

## 10. Файли, змінені в цьому циклі

- `apps/web/src/components/ui/logo.tsx` — новий логотип (Терези рівноваги).
- `apps/web/src/components/reference/shell.tsx` — логотип + статистика БД у чіпі.
- `apps/web/src/app/uk/page.tsx` — реальні лічильники з `/stats`.
- `apps/web/src/app/uk/legislation/page.tsx` — реальний пошук/список з `/documents`.
- `apps/web/src/styles/globals.css` — виправлення скролу (`min-height:0`).
- `docs/STATUS_AUDIT.md`, `docs/SITE_ANALYSIS.md` — документація.

---

**Висновок:** сайт працює, дані завантажуються, скрол виправлено, логотип оновлено. Основний борг — ruff, PostgreSQL, auth/rate-limiting і незаповнені сторінки.

