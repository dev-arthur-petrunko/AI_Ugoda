# Журнал розробки AI Ugoda

## 23.10.2026 — Початок реалізації (Фаза 0 + частина Фази 1)

### Зроблено
- Аудит репозиторію: тека порожня (greenfield).
- Перевірка zakon.rada.gov.ua: сторінки доступні, CC BY 4.0, база інформаційна, RSS-сторінка — HTML-обгортка (чистий XML не підтверджено).
- Перевірка data.rada.gov.ua: list.json валідний, оновлення щогодини, формати CSV/JSON/XML.
- Створено монOREPO:
  - apps/api/requirements.txt, Dockerfile
  - apps/api/app/core/config.py, app/core/database.py, app/main.py
  - Моделі SQLAlchemy: LegalDocument, DocumentRevision, LegalProvision, LegalEvent, LegalReference, LegalLink, LegalForceLevel, AIAnalysis, ConflictCandidate, User, UserMonitoringRule, UserBookmark, ContractDocument, ContractAnalysis, AuditLog
  - Alembic міграції 0001_initial_schema.py та 0002_extend_schema.py (повна схема з індексами, обмеженнями, рівнями юридичної сили, зв'язками між нормами)
  - API ендпоінти: /health, /api/v1/documents (list/get), /api/v1/sync (run/status для обох джерел)
  - Сервіс імпорту ImportService (ідемпотентний upsert документів, ревізій, положень, зв'язків, колізій)
  - Детектор колізій ConflictEngine (HIERARCHY_CONFLICT, SAME_LEVEL_NEWER, DEAD_REFERENCE)
  - Коннектори data.rada.gov.ua (основне) + zakon.rada.gov.ua (запасне)
  - docker-compose.yml (Postgres, Redis, API, Web, Worker), .env.example, .gitignore
  - Фронтенд: Next.js 14, Tailwind, дизайн Black Coffee Gold, логотип з анімацією, заставка, адаптивна навігація, дашборд, сторінки всіх розділів
  - Юніт-тести: 6 тестів (ImportService + ConflictEngine) — всі проходять
- Документація: README.md, docs/PHASE_0_AUDIT.md, docs/DEVLOG.md, docs/SOURCES_VERIFIED.md

### Не зроблено (баклог)
- Реальний імпорт документів з data.rada.gov.ua / zakon.rada.gov.ua у PostgreSQL (seed_acts.py створено, потребує БД)
- AI/RAG, підключення LLM (Groq/OpenAI/Anthropic)
- Завантаження та аналіз договорів (PDF/DOCX/TXT)
- JWT автентифікація та RBAC
- Сповіщення моніторингу (in-app/email/Telegram)
- Експорт звітів (PDF/DOCX)
- Пуш на GitHub (потрібен PAT користувача arthurpetrunko@gmail.com)

### Далі
- Імпорт 5 тестових актів (Конституція, Цивільний кодекс, Кримінальний кодекс, КЗпП, Податковий кодекс) через scripts/seed_acts.py
- Розширення детектора колізій (GHOST_NORM, CODE_DUPLICATION, UNCONSTITUTIONAL, EXPIRING)
- Потім пуш у https://github.com/dev-arthur-petrunko/AI_Ugoda (потрібен PAT користувача arthurpetrunko@gmail.com).
