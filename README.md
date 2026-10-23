# AI Ugoda — Юридична інтелектуальна платформа

Законодавство України — зрозуміле, актуальне та пов'язане. Від офіційного тексту до практичного аналізу.

## Стан реалізації (поточний)

Реалізовано **Фазу 0 (аудит)** та частину **Фази 1 (дизайн-система та оболонка)**:

- Бекенд: FastAPI + SQLAlchemy + Alembic (PostgreSQL), версійно-świadома схема даних (акти, ревізії, положения, події, посилання, аналізи, колізії, користувачі, моніторинг, договори, аудит).
- Коннектор офіційного джерела zakon.rada.gov.ua з перевіркою досяжності та чіткою позначкою обмежень (чесний порожній стан, без вигаданих даних).
- Фронтенд: Next.js + Tailwind, чорно-золота дизайн-система, адаптивна навігація, дашборд, сторінки всіх розділів spécifications.
- Інфраструктура: Docker Compose (PostgreSQL, Redis, API, Web, Worker).
- Не реалізовано ще: реальний імпорт документів з zakon.rada.gov.ua, AI/RAG, завантаження договорів, автентифікація JWT, сповіщення.

## Швидкий старт (Docker)

```bash
# 1. Скопіювати змінні середовища
cp .env.example .env
# відредагуйте .env при потребі (SECRET_KEY, AI_PROVIDER тощо)

# 2. Запустити сервіси
docker compose up --build

# 3. Відкрити
# Web:  http://localhost:3000
# API:  http://localhost:8000 (документація /api/v1/docs)
# Health: http://localhost:8000/health
```

Команди:
```bash
docker compose up -d          # у тлі
docker compose logs -f api    # логи бекенду
docker compose down           # зупинка
docker compose exec api alembic upgrade head  # міграції (запускаються автоматично при старті API)
```

## Змінні середовища

Див. `.env.example`. Обов'язково змініть `SECRET_KEY` перед продакшном.

## Вдали github

Репозиторій призначений для пушу від користувача `arthurpetrunko@gmail.com`:
`https://github.com/dev-arthur-petrunko/AI_Ugoda.git`

Потрібен GitHub personal access token (PAT) з правом `repo`.

## Обмеження (чесний стан)

- Жодних документів zakon.rada.gov.ua ще не імпортовано.
- Жодних вигаданих статистик — дашборд показує нулі з поясненням.
- AI не підключено до реальних даних (AI_PROVIDER=mock за замовчуванням).
- Чистий RSS-XML ендоポイント zakon.rada.gov.ua не підтверджено як стабільний публічний API.

Див. `docs/PHASE_0_AUDIT.md` та `docs/DEVLOG.md`.