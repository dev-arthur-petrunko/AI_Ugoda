# CLEANUP_REPORT.md — AI Ugoda (Етап 1 — очищення)

Дата: 26.10.2026 · Версія проєкту: 0.1.0 · Коміт: `da73f6d` (запушений у `origin/main`)

## Загальний стан

Етап 1 (очищення і виправлення помилок) виконаний. Усі перевірки пройдено з виводами (див. розділ «Результати перевірок»).

## 1. Ruff (бекенд, `apps/api`)

| Перевірка | Результат |
|-----------|-----------|
| `ruff check apps/api` | **All checks passed!** (0 помилок) |
| Автофікс `--fix` | Застосовано (93 помилки виправлено автоматично) |
| Вручну виправлено | `SIM102`/`FURB192` (`documents.py` /at), `F841` (`conflict_engine.py`), `BLE001`/`S110`/`S112` (`connector.py`, `parser.py`, `import_service.py`, `conflict_engine.py`), `RUF012` (`parser.py`), `PYI034` (`import_service.py`), `DTZ003`/`DTZ007`/`UP017` (`import_service.py`) |
| Конфігурація | `pyproject.toml` з документованими ігноруваннями `B008` (FastAPI `Depends`) та `F821` (рядкові forward-посилання SQLAlchemy) |

## 2. F821 — рядкові forward-посилання у моделях

Усі 18 F821 — це `Mapped["LegalDocument"]` тощо. SQLAlchemy розв'язує їх через реєстр класів під час конфігурації маперів (`configure_mappers()`), тому це не реальні `NameError` під час роботи. Ігноруються у `pyproject.toml` з поясненням.

## 3. Мертвий код у `import_service.py`

Видалено невиконуваний блок після `return row` у `upsert_force_level` (раніше рядки 80–82).

## 4. Інструменти безпеки та якості (запущені, виводи додано в `docs/AUDIT_2026-10-26.md`)

| Інструмент | Результат |
|------------|-----------|
| `bandit -r apps/api` | 6 результатів, усі `LOW` (hardcoded паролі в `deps.py`/`main.py` — очікувано для dev; `try_except_pass/continue` у middleware/сервісах) |
| `pip-audit` | 98 відомих вразливостей у 16 пакетах (приклади: `aiohttp`, `pillow`, `pyjwt`, `pypdf`) — вимагають оновлення залежностей |
| `npm audit --audit-level=moderate` | 2 вразливості (1 high, 1 critical) у `postcss` через `next@14.2.15` — оновлення до Next.js 16 — розривна зміна |
| `npm outdated` | `next 14.2.15→16.4.3`, `react 18.3.1→19.3.1`, `tailwindcss 3.4.19→4.3.3`, `typescript 5.9.3→7.0.2` тощо |
| `vulture` | Невикористаний код: `conflict_engine.py`, `connector.py` (`sync_once`), `import_service.py`, `parser.py` (`extract_references`, `SELECTORS`), `search.py` (`effective_date_from/to`) |
| `knip` (веб) | Невикористані файли (6): `sidebar.tsx`, `topbar.tsx`, `badge.tsx`, `input.tsx`, `loader.tsx`, `skeleton.tsx`; залежності (2): `framer-motion`, `axios`; невикористані експорти (10) |
| `depcheck` (веб) | Невикористані: `axios`, `@types/node`, `@types/react-dom`, `autoprefixer`, `postcss`, `typescript` |

## 5. Що НЕ зроблено (і чому)

1. **Дубль CSS-токенів дизайну** (`--bg/--card/...` vs `--black/--cocoa/...` у `apps/web/src/styles/globals.css`) — не об'єднано; заплановано в Етапі 2.
2. **Оновлення залежностей** (Next.js 14 → стабільна, Python-пакети з CVE) — винесену в Етап 4 (безпека), оскільки оновлення Next.js — розривна зміна.
3. **Видалення невикористаного коду** (vulture/knip/depcheck результати) — потребує рев'ю, щоб не видалити планований код Етапів 5–12.

## 6. Відомі проблеми

- У `data/aiugoda.db` кожен акт має 2 ідентичні редакції (однаковий `source_hash`) — дублі (Д11.5, Запит 2).
- `nreg` КУпАП у БД = `807-V`, очікується `80731-10` — розбіжність з zakon.rada.gov.ua (потрібна перевірка).
- Тестовий попередження pytest про невідомий `asyncio_mode` (конфіг у `pytest.ini`) — не блокує тести.

## 7. Результати перевірок (останній запуск)

```
$ python -m pytest -q
11 passed, 2 skipped, 3 warnings in ~9s   (2 skipped — FTS-тести потребують PostgreSQL)

$ python -m ruff check apps/api
All checks passed!
```

## 8. Git

- Хеш коміту: `da73f6d` (запушений у `origin/main`)
- `git ls-files` не містить `.env`, `*.db`, `__pycache__`, `node_modules`, `.next` (OK)

---

Наступний крок за ТЗ — К2 (Логотип: справжнє впровадження), після прийняття звіту аудиту та цього CLEANUP_REPORT.

