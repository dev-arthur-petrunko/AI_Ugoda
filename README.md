# AI Ugoda — Юридична інтелектуальна платформа

Законодавство України: пошук, аналіз колізій, AI-допомога з цитуваннями.

## Документація (3 файли)

| Файл | Вміст |
|---|---|
| [`docs/STATUS.md`](docs/STATUS.md) | Що працює · що ще не зроблено · відомі проблеми |
| [`docs/PROJECT_FULL_REPORT.md`](docs/PROJECT_FULL_REPORT.md) | Архітектура, БД, ендпоінти, інтерфейс, анімації, аналізи й обчислення, AI-промти, безпека, тести |
| [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Запуск, конфіги, експлуатація імпорту, діагностика, план робіт |

## Швидкий старт

```powershell
docker compose up -d postgres redis
cd apps/api  # alembic upgrade head; uvicorn app.main:app --reload --port 8000
cd apps/web  # npm install; npm.cmd run dev  →  http://localhost:3000/uk
```

Деталі — в `docs/OPERATIONS.md`.
