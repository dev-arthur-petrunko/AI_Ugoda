# 📁 Операційна документація AI Ugoda

Цей файл призначений для агентів і розробників, які працюють над проєктом. В ньому чітко зафіксовано: де зберігається база даних, що є «сміттям» (тимчасовими файлами), а також рівень безпеки поточного релізу.

---

## 1. Де зберігається база даних

### Режим розробки (зараз активний)
- **Активна БД:** PostgreSQL 16 (Docker, контейн `aiugoda_postgres`) — зараз працює саме вона.
- **Резерв/dev:** SQLite `apps/api/test.db` або `data/aiugoda.db` — використовується **лише тестами** (TestClient override на SQLite in-memory).
- **⚠️ `data/aiugoda.db` застарів** (немає `alembic_version` і колонки `legal_provisions.embedding`): запуск uvicorn проти SQLite дає **500** на `/api/v1/stats`. Не використовуйте його як робочу БД — активна БД тільки PostgreSQL.
- **Змінна середовища:** `DATABASE_URL` у файлі `.env` (корінь проєкту)
- **Приклад (PostgreSQL):** `DATABASE_URL=postgresql+psycopg2://aiugoda:aiugoda@localhost:5432/aiugoda`

**Як перевірити, де зараз лежить БД:**
```powershell
python -c "import sys; sys.path.insert(0, r'C:\Users\Arthur\Desktop\AI Ugoda\apps\api'); from app.core.config import settings; print(settings.DATABASE_URL)"
```

### Режим продакшну (Docker)
- **Тип:** PostgreSQL 16 (контейнер `aiugoda_postgres`, образ `pgvector/pgvector:pg16` + hunspell-uk).
- **Об'єм даних:** volume `aiugoda_postgres_data` (Dashboard Docker або `docker volume ls`).
- **Змінна середовища:** `DATABASE_URL=postgresql+psycopg2://aiugoda:aiugoda@postgres:5432/aiugoda` (усередині мережі Docker).
- **Запуск:** `docker compose up --build` (API виконує `alembic upgrade head` при старті).
- **Міграції:** `0001_initial_schema`, `0002_extend_schema`, `0003_pgvector_fts`, `0004_unique_constraints`, `0005_ukrainian_fts`.

> **Правило:** ніколи не пишите жорстко задані шляхи до `C:\Users\...` у коді бекенду. У `app/core/database.py` шлях до SQLite розв'язується відносно поточного файлу конфігурації через `pathlib.Path.resolve()`.

---

## 2. Що є «сміттям» / тимчасовими файлами (можна видаляти)

Наступні файли та папки безпечно видаляти, вони відновлюються автоматично або не несуть цінних даних:

| Шлях | Що це | Можна видаляти? |
|------|-------|-----------------|
| `apps/api/__pycache__/` | Скомпільований Python-код | ✅ Так |
| `apps/web/.next/` | Збірка Next.js | ✅ Так |
| `apps/web/node_modules/` | Залежності npm | ✅ Так (повернути через `npm install`) |
| `.pytest_cache/` | Кеш тестів pytest | ✅ Так |
| `*.pyc`, `*.pyo` | Байт-код Python | ✅ Так |
| `api.out.log`, `api.err.log` | Логи запуску uvicorn (локально) | ✅ Так |
| `debug*.py`, `debug_err.txt` | Тимчасові скрипти налагодження | ✅ Так (не комітити) |

### ⚠️ НЕ видаляти (ціповані дані / секрети)
- `data/aiugoda.db` — база даних SQLite (всі акти, користувачі, колізії)
- `apps/api/alembic/versions/0001_initial_schema.py` — міграція БД
- `apps/api/alembic/versions/0002_extend_schema.py` — міграція БД (ТЗ v2)
- `.env` — змінні середовища (містить `SECRET_KEY`, ключі AI, паролі) — **не публікувати в git**
- `docker-compose.yml` — конфігурація інфраструктури

---

## 3. Рівень безпеки (поточний стан)

Проєкт знаходиться на **Фазі 2 (прототип даних)**. Чесний статус:

| Компонент | Статус | Деталі |
|-----------|--------|--------|
| **База даних** | ✅ Готово | PostgreSQL 16 (Docker) з Ukrainian FTS; SQLite — лише для тестів; 5 сід-актів імпортовано |
| **Імпорт актів** | ✅ Готово | `/sync/run` → `sync_once()`: парсинг zakon.rada.gov.ua (K4) |
| **Деталі акта / diff** | ✅ Готово | `/documents/{id}/at?date=`, `/documents/{id}/diff` (K8) |
| **Повнотекстовий пошук** | ✅ Готово | Ukrainian FTS (tsquery + GIN, конфігурація `ukrainian`) |
| **Детектор колізій** | ✅ Готово | 5 типів (HIERARCHY, SAME_LEVEL_NEWER, DEAD_REFERENCE, EXPIRING, GHOST_NORM) |
| **ІІ / RAG** | ⚠️ Частково | `/ai/ask` працює; реальний провайдер потребує ключа в `.env` (зараз `AI_PROVIDER=mock`) |
| **Rate limiting** | ✅ Готово | Per IP, sliding window, Redis + in-memory fallback, 120 req/min |
| **Автентифікація** | ✅ Готово | JWT (jose, декодування, ролі user/admin) у `deps.py`; `/api/v1/stats` — публічний; захищені ендпоінти віддають 401 |
| **Заголовки безпеки** | ✅ Готово | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy (middleware у `main.py`) |

Нижче наведено чесний огляд безпеки:

### ❌ НЕ реалізовано (не робити в продакшні без виправлення)
| Проблема | Де | Статус |
|----------|----|--------|
| `SECRET_KEY=dev-secret-change-me` | `.env` | ⚠️ Змінити перед продакшном |
| `COOKIE_SECURE=false` | `.env` | ⚠️ Куки не зашифровані |
| Реальний LLM-провайдер | `ai_service.py` | ⚠️ Потрібен ключ (`GROQ_API_KEY` etc.) у `.env`; зараз `AI_PROVIDER=mock` |
| CVE у залежностях | pip-audit / npm audit | ⚠️ Потрібні оновлення пакетів |
| Юридичне рев'ю (K12) | — | ⚠️ Очікує підпису юриста (див. STATUS.md, розділ «Юридичне рев'ю K12») |

### ✅ Реалізовано з безпеки
- CORS (тільки `http://localhost:3000` у розробці); **UI працює same-origin** (`API_BASE=""` + rewrites Next.js) — CORS для фронтенду не потрібен
- SQL-ін'єкції: параметризовані запити SQLAlchemy (тести `test_sql_injection.py`)
- JWT / RBAC: `deps.py` (декодування токена, ролі user/admin, перевірка `is_superuser`)
- Rate limiting: Redis + in-memory fallback, 120 req/min
- Заголовки безпеки: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- Завантажені файли договорів хешуються (`secure_storage_key`); вміст поки не шифрується
- Аудитний журнал (`audit_logs`) без запису повного тексту договорів

### Рекомендація агенту
- Не додавайте нових секретів у `.env` або у код — використовуйте змінні середовища.
- При тестуванні не надсилайте реальні тек스트 договорів через `AI_PROVIDER=groq/openai/anthropic`, якщо ключ не додано (зараз `mock`).
- При пуші в GitHub переконайтеся, що `.env` додано у `.gitignore` (вже додано).

---

## 4. Як запустити проєкт локально (чекулист)

```powershell
# 1. Перейти в корінь проєкту
cd "C:\Users\Arthur\Desktop\AI Ugoda"

# 2. Переконатися, що .env існує (створити з .env.example, якщо немає)

# 3. База даних + Redis (Docker)
docker compose up -d postgres redis
# Міграції (або автоматичний `alembic upgrade head` при старті api в docker compose)
cd apps\api; alembic upgrade head; cd ..\..

# 4. (Опційно) імпорт тестових актів: 5 шт. (Конституція, Цивільний, Кримінальний, КУпАП, Податковий)
python apps/api/scripts/seed_acts.py

# 5. Бекенд (uvicorn) — робоча директорія apps/api
cd apps\api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 6. Фронтенд (Next.js) — окремий термінал, робоча директорія apps/web
cd apps\web
npx next build       # production
npx next start -p 3000
# або для розробки: npm run dev

# 7. Перевірити
# http://127.0.0.1:8000/health          -> {"status":"ok"}
# http://127.0.0.1:8000/api/v1/stats     -> {"documents":5,...} (публічний)
# http://127.0.0.1:8000/api/v1/documents?limit=50 -> total == кількість items (без дублів)
# http://127.0.0.1:3000/uk               -> 200
# http://127.0.0.1:3000/api/v1/stats     -> 200 (прокси same-origin, CORS не потрібен)
# /conflicts без слеша віддає 307 -> /conflicts/ (штатний trailing-slash FastAPI), за ним 200

# 8. Тести (з кореня проєкту, не з apps/api!)
cd "C:\Users\Arthur\Desktop\AI Ugoda"
python -m pytest -q        # 23 passed, 2 skipped
ruff check apps/api        # 0 помилок
```

---

## 5. Що робити, якщо база даних «зникла» або пише «unable to open database file»

1. Перевірити, що файл існує: `C:\Users\Arthur\Desktop\AI Ugoda\data\aiugoda.db`
2. Якщо файлу немає — виконати `python apps/api/scripts/init_db.py`
3. Якщо файл є, але помилка доступу — переконатися, що робоча директорія uvicorn вказана як `apps/api`, а шлях до БД у `.env` є абсолютним (`sqlite:///C:/Users/Arthur/Desktop/AI Ugoda/data/aiugoda.db`)
4. Перезапустити uvicorn після змін у `.env`

---

## 6. Документація проєкту (усього 3 файли)

- `README.md` — загальний огляд проєкту (корінь репозиторію)
- `docs/STATUS.md` — статус: що зроблено (K1–K12), останні зміни, юридичне рев'ю K12, Git
- `docs/PROJECT_FULL_REPORT.md` — архітектура, БД, автентифікація, пошук, фронтенд, Docker, тести, зміни
- `docs/OPERATIONS.md` — цей файл: БД, тимчасові файлі, безпека, запуск, troubleshooting

---

**Останнє оновлення:** 04.11.2026  
**Автор:** Arthur Petrunko <arthurpetrunko@gmail.com>