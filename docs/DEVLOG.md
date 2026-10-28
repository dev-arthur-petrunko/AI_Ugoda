# Журнал розробки AI Ugoda

# Журнал розробки AI Ugoda

## 26.10.2026 — К1: доведення Етапу 1 до кінця (очищення)

### Зроблено
- **Авторизація виправлена:** `AUTH_DISABLED OR APP_ENV=development` → `AUTH_DISABLED AND APP_ENV=development`; `AUTH_DISABLED=False` за замовчуванням; анонімний користувач без прав адміна (`is_superuser: False`).
- **Мертвий код видалено:** невиконуваний блок після `return row` у `import_service.py:upsert_force_level`.
- **Тести додано:** `tests/test_auth.py` (401 без токена), `tests/test_import_service.py` (тест N статей → N у БД, ідемпотентність).
- **Інструменти якості запущені:** ruff 0 помилок; bandit 6 LOW; pip-audit 98 CVE; npm audit 2 (postcss); knip/depcheck/vulture виводи додано в AUDIT_2026-10-26.md.
- **Звіт аудиту:** `docs/AUDIT_2026-10-26.md` створено з сировими виводами команд (A1–A10.1).
- **Звіт очищення:** `docs/CLEANUP_REPORT.md` оновлено.
- **Пуш на GitHub:** виконано, коміт `da73f6d` запушений у `origin/main` (автор: Arthur Petrunko <arthurpetrunko@gmail.com>).

### Тести
- `python -m pytest -q` → 11 passed, 2 skipped (FTS потребує PostgreSQL + Hunspell).
- `python -m ruff check apps/api` → All checks passed!

### Бакалоблоки
- Оновлення залежностей (Next.js 14 → 16, CVE Python-пакетів) — Етап 4.
- Об'єднання двох шкал CSS-токенів — Етап 2.
- Docker Desktop не запущено → неможливо валідувати FTS/міграції/збірку образу.

