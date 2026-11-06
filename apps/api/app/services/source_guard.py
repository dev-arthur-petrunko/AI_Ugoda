"""
S3.3 — охорона джерел: білий список хостів, HTTPS, ввічливість, статус, кеш.

Правила (план S3, розділ «Правила»):
- тексти актів лише з data.rada.gov.ua і zakon.rada.gov.ua (білий список,
  перевірка двічі: перед запитом і перед записом);
- не частіше 1 запиту на секунду, User-Agent: AIUgodaBot/0.1 (+контакт);
- кеш сирих відповідей (raw_payload + SHA-256): повторні запуски нічого зайвого не качають;
- статус джерела: active / degraded / down + last_ok_at + текст помилки;
- SourceNotAllowed → запис в audit_logs (правило: жодних «тихих» except).
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from datetime import UTC, datetime
from urllib.parse import urlparse

logger = logging.getLogger("aiugoda.sources")

ALLOWED_HOSTS: frozenset[str] = frozenset({"data.rada.gov.ua", "zakon.rada.gov.ua"})
ALLOWED_SCHEMES: frozenset[str] = frozenset({"https"})
USER_AGENT = "AIUgodaBot/0.1 (contact: arthurpetrunko@gmail.com)"
MIN_REQUEST_INTERVAL_S = 1.0  # ввічливість: не частіше 1 запиту на секунду


class SourceNotAllowed(Exception):
    """URL не з білого списку джерел або не https."""


def validate_url(url: str, *, stage: str = "request") -> str:
    """Перевірка URL (двічі: stage='request' перед запитом, stage='write' перед записом)."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SourceNotAllowed(f"[{stage}] недопустима схема {parsed.scheme!r} для {url!r}: дозволено лише https")
    if host not in ALLOWED_HOSTS:
        raise SourceNotAllowed(f"[{stage}] хост {host!r} не в білому списку: {sorted(ALLOWED_HOSTS)}")
    return url


def log_source_not_allowed(url: str, *, stage: str, db=None) -> None:
    """Запис SourceNotAllowed в audit_logs (і лог). Не кидає винятків назовні."""
    message = f"SourceNotAllowed [{stage}]: {url}"
    logger.warning(message)
    if db is None:
        return
    try:
        from app.models.audit_log import AuditLog

        db.add(
            AuditLog(
                action="source_not_allowed",
                target_type="source_url",
                metadata_json={"url": url, "stage": stage},
            )
        )
        db.commit()
    except Exception:
        logger.exception("не вдалося записати audit_log для %s", url)
        db.rollback()


class _RateLimiter:
    """Глобальний ліміт: не частіше 1 запиту на секунду (міжпроцесний не потрібен — один uvicorn)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> float:
        with self._lock:
            now = time.monotonic()
            delta = now - self._last
            if delta < MIN_REQUEST_INTERVAL_S:
                sleep_for = MIN_REQUEST_INTERVAL_S - delta
            else:
                sleep_for = 0.0
            self._last = now + sleep_for
        if sleep_for:
            time.sleep(sleep_for)
        return sleep_for


rate_limiter = _RateLimiter()

# Кеш сирих відповідей: sha256(url) -> (sha256(raw), raw, fetched_at)
_raw_cache: dict[str, tuple[str, str, str]] = {}


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def get_cached_raw(url: str) -> tuple[str, str, str] | None:
    """Повертає (content_sha256, raw, fetched_at), якщо відповідь уже кешована."""
    return _raw_cache.get(cache_key(url))


def put_cached_raw(url: str, raw: str) -> tuple[str, str]:
    """Кешує сиру відповідь; повертає (content_sha256, fetched_at)."""
    content_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    fetched_at = datetime.now(UTC).isoformat()
    _raw_cache[cache_key(url)] = (content_sha, raw, fetched_at)
    return content_sha, fetched_at


def raw_cache_stats() -> dict[str, int]:
    return {"entries": len(_raw_cache)}


# Статуси джерел: host -> dict(status, last_ok_at, last_error, checks, failures)
_source_status: dict[str, dict] = {
    host: {"status": "unknown", "last_ok_at": None, "last_error": None, "checks": 0, "failures": 0}
    for host in sorted(ALLOWED_HOSTS)
}


def record_source_result(url: str, *, ok: bool, error: str | None = None) -> dict:
    """Оновлює статус джерела: active (усе гаразд), degraded (були помилки), down (серія помилок)."""
    host = (urlparse(url).hostname or "").lower()
    st = _source_status.get(host)
    if st is None:
        # хост поза білим списком — не підміняємо статус відомих джерел
        return {"status": "unknown", "last_ok_at": None, "last_error": f"unknown host {host!r}", "checks": 0, "failures": 0}
    st["checks"] += 1
    if ok:
        st["status"] = "active"
        st["last_ok_at"] = datetime.now(UTC).isoformat()
        st["last_error"] = None
        st["failures"] = 0
    else:
        st["failures"] += 1
        st["last_error"] = error or "unknown error"
        # 3+ поспіль помилки або жодного успіху → down, інакше degraded
        st["status"] = "down" if (st["failures"] >= 3 or st["last_ok_at"] is None) else "degraded"
    return dict(st)


def source_statuses() -> dict[str, dict]:
    return {host: dict(st) for host, st in _source_status.items()}
