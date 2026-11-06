"""
S3.3 — лічильники імпорту: кожна помилка розбору лічиться й потрапляє у звіт.

Правило 2 (план S3): жодних «тихих» except: pass; кількість помилок → звіт запуску.
"""

from __future__ import annotations

import threading

_lock = threading.Lock()
_parse_errors: list[dict] = []


def record_parse_error(message: str, *, source_url: str | None = None) -> int:
    """Реєструє помилку парсингу; повертає поточну кількість. Не кидає винятків."""
    with _lock:
        _parse_errors.append({"message": message, "source_url": source_url})
        return len(_parse_errors)


def parse_errors() -> list[dict]:
    with _lock:
        return list(_parse_errors)


def parse_error_count() -> int:
    with _lock:
        return len(_parse_errors)


def reset_parse_errors() -> None:
    with _lock:
        _parse_errors.clear()
