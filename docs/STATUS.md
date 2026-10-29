# AI Ugoda — Статус проєкту (повний звіт)

Дата: 29.10.2026
Автор: Arthur Petrunko <arthurpetrunko@gmail.com>
Гілка: main @ e02e571 (запушений у origin/main)

## 1. Загальний стан

AI Ugoda — юридична інтелектуальна платформа для роботи з законодавством України.
Проєкт знаходиться на стадії K1 (доведення Етапу 1 до кінця).

## 2. Виконані кроки (K1)

### K1.1 Auth Fix (A4)
- `deps.py`: `AUTH_DISABLED AND APP_ENV=development` (було `OR`)
- `AUTH_DISABLED=False` за замовчуванням
- Анонімний користувач — `is_superuser: False`, роль `user`
- Тест `test_auth.py`: 401 без токена ✅

### K1.2 Мертвий код
- `import_service.py:80-82` — видалено невиконуваний блок

### K1.3 Звіти та документація
- `docs/AUDIT_2026-10-26.md` — звіт з сировими виводами команд
- `docs/CLEANUP_REPORT.md` — звіт очищення Етапу 1
- `docs/SITE_ANALYSIS.md` — оновлений аналіз сайту
- `docs/PROJECT_FULL_REPORT.md` — всесвідомлюючий звіт про проєкт
- `docs/DEVLOG.md` — журнал розробки
- `docs/OPERATIONS.md` — операційна документація
- `README.md` — оновлено
- `docs/PROJECT_DOCUMENTATION.md` — всесвідомлюючий проєктний документ

### K1.4 Тести та якість
- `pytest -q`: **11 passed, 2 skipped** (FTS тести потребують PostgreSQL + Hunspell)
- `ruff check`: **0 помилок**
- `bandit`: **6 LOW** (hardcoded паролі у dev, `try_except_pass`)
- `pip-audit`: **98 CVE у 16 пакетах**
- `npm audit`: **2 вразливості**

### K1.5 Логотип (K2)
- `components/brand/Logo.tsx` — компонент з варіантами `mark` / `lockup` / `seal`
- `components/brand/Splash.tsx` — заставка (SessionStorage, ≤ 2.2 с)
- `app/icon.svg` — SVG логотип для favicon
- Підключено: `layout.tsx`, `sidebar.tsx`, `shell.tsx`, `loader.tsx`

### K1.6 База даних (K3)
- PostgreSQL 16 + pgvector + pg_trgm (Docker)
- Ukrainian FTS: конфігурація `ukrainian` + Hunspell словник `uk_UA`
- UNIQUE constraints: nreg, revision+hash, provision+identifier
- Дублі редакцій видалено (5 актів, по 1 редакції)
- Alembic version: `0005_ukrainian_fts`

### K1.7 Імпорт даних (K4)
- `seed_acts.py` — імпорт 5 тестових актів (Конституція, Цивільний, Кримінальний, КУпАП, Податковий кодекси)
- `upsert_revision` функція виправлена (перевірка по `source_hash`)
- nreg КУпАП: `807-V` (очікується `80731-10` — розбіжність, потрібно свернити)
- Джерела лише з `zakon.rada.gov.ua` (Д9 дотримується)
- data.rada.gov.ua доступне (200 OK, JSON підтвердженний)

## 3. Не виконані завдання

### K2-K12 (блокери)
| Крок | Назва | Статус | Причина |
|------|-------|--------|---------|
| K2 | Логотип: справжнє впровадження | ⚠️ Частково | Логотип інтегровано, але немає скріншотів (9 місць) |
| K3 | PostgreSQL + обмеження унікальності | ✅ Виконано | UNIQUE constraints додано, alembic stamped |
| K4 | Реальний імпорт Tier 1 | ⚠️ Частково | seed_acts.py працює, але дані тестові |
| K5 | Сторінка акта + 9 розділів + дашборд | ❌ Не виконано | Плейсхолдери не довобудовані |
| K6 | Базова аналітика акта | ❌ Не виконано | Вкладка «Аналіз» не реалізована |
| K7 | Безпека (JWT, rate limit, CSRF) | ⚠️ Частково | Rate limiting реалізовано, JWT/CSRF/CSP — ні |
| K8 | Пошук «на дату», diff, гібридний пошук | ⚠️ Частково | `/at` є, diff-ендпоінт відсутній |
| K9 | Зв'язки, колізії, ризик | ⚠️ Частково | conflict_engine.py є, але risk-модуль відсутній |
| K10 | ШІ та ІІ-аналізи | ❌ Не виконано | AI_PROVIDER=mock, RAG-конвеєр — відсутній |
| K11 | Акаунти, моніторинг, договори | ❌ Не виконано | JWT/ролі, підписки, аналіз договорів — не реалізовані |
| K12 | Якість і право | ❌ Не виконано | Навантажувальні тести, юридичне рев'ю — не виконані |

## 4. Технічні деталі

### 4.1 Логотип (K2)
- `components/brand/Logo.tsx` — variants: `mark`, `lockup`, `seal`
- `components/brand/Splash.tsx` — заставка (SessionStorage, 2.2с)
- `app/icon.svg` — SVG логотип (160×160, scales)
- Підключено: `layout.tsx`, `sidebar.tsx`, `shell.tsx`, `loader.tsx`

### 4.2 База даних (K3)
- PostgreSQL 16 + pgvector + pg_trgm (Docker)
- Ukrainian FTS: конфігурація `ukrainian` + Hunspell словник `uk_UA`
- UNIQUE constraints: nreg, revision+hash, provision+identifier
- Alembic version: `0005_ukrainian_fts`

### 4.3 Імпорт (K4)
- `seed_acts.py` — імпорт 5 тестових актів
- `upsert_revision` виправлена (перевірка по source_hash)
- nreg КУпАП: `807-V` (очікується `80731-10` — розбіжність, потрібно свернити)
- Джерела лише з `zakon.rada.gov.ua` (Д9 дотримується)
- data.rada.gov.ua доступне (200 OK, JSON підтвердженний)

### 4.4 Безпека (K7)
- CORS: тільки `http://localhost:3000`
- SQL-ін'єкції: параметризовані запити
- Rate limiting: Per IP, sliding window, Redis + in-memory fallback
- SECRET_KEY перевірка: у продакшені не дозволяється `dev-secret-change-me`
- JWT / RBAC: ❌ не реалізовано
- CSRF / CSP: ❌ не реалізовано

### 4.5 Тестування
- pytest: 11 passed, 2 skipped (FTS потребує PostgreSQL)
- ruff: 0 помилок
- bandit: 6 LOW
- pip-audit: 98 CVE у 16 пакетах
- npm audit: 2 вразливості (postcss)

## 5. Файли проєкту (без секретів)

### 5.1 Документація (`docs/`)
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

### 5.2 Бекенд (`apps/api/`)
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
| `app/models/*.py` | SQLAlchemy моделі (17 таблиць) |

### 5.3 Фронтенд (`apps/web/src/`)
| Файл | Опис |
|------|------|
| `components/brand/Logo.tsx` | Логотип «Терези рівноваги» |
| `components/brand/Splash.tsx` | Заставка (SessionStorage) |
| `app/layout.tsx` | Кореневий layout з логотипом |
| `components/nav/sidebar.tsx` | Сайдбар з логотипом |
| `components/reference/shell.tsx` | Оболонка з логотипом |
| `app/icon.svg` | SVG логотип для favicon |

### 5.4 Docker
| Файл | Опис |
|------|------|
| `docker-compose.yml` | 5 сервісів (postgres, redis, api, web, worker) |
| `docker/postgres/Dockerfile` | pgvector + hunspell-uk |
| `docker/postgres/init/01_ukrainian_fts.sql` | Ініціалізація Ukrainian FTS |

### 5.5 Тести
| Файл | Опис |
|------|------|
| `tests/conftest.py` | Фікстури (SQLite in-memory) |
| `tests/test_auth.py` | Тест 401 без токена |
| `tests/test_import_service.py` | Тест ідемпотентності |
| `tests/test_conflict_engine.py` | Тест колізій |
| `tests/test_fts_ukrainian.py` | Тест FTS (PostgreSQL) |
| `tests/test_sql_injection.py` | Тест SQL-ін'єкцій |

## 6. Правила безпеки (ТЗ)

1. **Секрети лише в `.env`** — не в коді, не в git
2. **`.env` і `*.db` не в git** — `.gitignore` криє
3. **Авторизація за замовчуванням закрита** — `AUTH_DISABLED=False`
4. **Rate limiting** — Per IP, 120 req/min
5. **CORS** — тільки `http://localhost:3000`
6. **SQL-ін'єкції** — параметризовані запити

## 7. Запуск локально

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

## 8. Git

- **Репозиторій:** `https://github.com/dev-arthur-petrunko/AI_Ugoda`
- **Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>
- **Гілка:** `main`
- **Останній коміт:** `e02e571` (K1: auth fixes, dead code removal, documentation updates, project docs)
- **Робоче дерево:** чисте
- **Статус:** запушено у `origin/main`

---

**Дата:** 29.10.2026
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>