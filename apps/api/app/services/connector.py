"""
РљРѕРЅРЅРµРєС‚РѕСЂРё РѕС„С–С†С–Р№РЅРёС… РґР¶РµСЂРµР» Р·Р°РєРѕРЅРѕРґР°РІСЃС‚РІР° РЈРєСЂР°С—РЅРё (РўР— v2, СЂРѕР·РґС–Р» 1).
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass

from app.core.config import settings
from app.services.parser import ZakonRadaParser
from app.services.source_guard import (  # S3.3
    USER_AGENT,
    SourceNotAllowed,
    get_cached_raw,
    log_source_not_allowed,
    put_cached_raw,
    rate_limiter,
    record_source_result,
    validate_url,
)


@dataclass
class SourceCheck:
    reachable: bool
    status_code: int | None
    content_type: str | None
    note: str


class DataRadaConnector:
    """РљРѕРЅРЅРµРєС‚РѕСЂ РґР»СЏ data.rada.gov.ua вЂ” РІС–РґРєСЂРёС‚С– РґР°РЅС– Р·Р°РєРѕРЅРѕРґР°РІСЃС‚РІР° Р’Р ."""

    def __init__(self) -> None:
        self.base_url = settings.DATA_RADA_BASE_URL.rstrip("/")
        self.laws_list_url = settings.DATA_RADA_LAWS_LIST_URL
        self.timeout = settings.DATA_RADA_REQUEST_TIMEOUT
        self.max_retries = settings.DATA_RADA_MAX_RETRIES
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": USER_AGENT}  # S3.3: ввічливий UA з контактом
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check_source(self):
        try:
            validate_url(self.laws_list_url, stage="request")  # S3.3: білий список перед запитом
            rate_limiter.wait()
            client = await self._get_client()
            resp = await client.get(self.laws_list_url, follow_redirects=True)
            ct = resp.headers.get("content-type", "")
            is_json = "json" in ct.lower()
            record_source_result(self.laws_list_url, ok=resp.status_code < 400, error=None if resp.status_code < 400 else f"HTTP {resp.status_code}")
            return SourceCheck(
                reachable=resp.status_code < 400,
                status_code=resp.status_code,
                content_type=ct,
                note=(
                    "data.rada.gov.ua laws list reachable; JSON confirmed"
                    if is_json
                    else "data.rada.gov.ua reachable but unexpected content-type"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            record_source_result(self.laws_list_url, ok=False, error=str(exc))
            return SourceCheck(
                reachable=False,
                status_code=None,
                content_type=None,
                note=f"data.rada.gov.ua unreachable: {exc!s}",
            )

    async def fetch_laws_list(self):
        try:
            validate_url(self.laws_list_url, stage="request")  # S3.3
        except SourceNotAllowed as exc:
            log_source_not_allowed(self.laws_list_url, stage="request")
            return {"source_url": self.laws_list_url, "verified": False, "error": str(exc)}

        cached = get_cached_raw(self.laws_list_url)  # S3.3: кеш сирих відповідей
        if cached is not None:
            content_sha, raw, fetched_at = cached
            import json as _json
            return {
                "source_url": self.laws_list_url,
                "status_code": 200,
                "content_type": "application/json",
                "data": _json.loads(raw),
                "content_sha256": content_sha,
                "fetched_at": fetched_at,
                "verified": True,
                "cached": True,
            }

        client = await self._get_client()
        last_error = None
        for attempt in range(self.max_retries):
            try:
                rate_limiter.wait()  # S3.3: ≤1 запит/с
                resp = await client.get(self.laws_list_url, follow_redirects=True)
                resp.raise_for_status()
                data = resp.json()
                import json as _json
                content_sha, fetched_at = put_cached_raw(self.laws_list_url, _json.dumps(data, ensure_ascii=False))
                record_source_result(self.laws_list_url, ok=True)
                return {
                    "source_url": self.laws_list_url,
                    "status_code": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "data": data,
                    "content_sha256": content_sha,
                    "fetched_at": fetched_at,
                    "verified": True,
                }
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                record_source_result(self.laws_list_url, ok=False, error=str(exc))
                await asyncio.sleep(2 ** attempt)
        return {
            "source_url": self.laws_list_url,
            "verified": False,
            "error": last_error,
        }

class ZakonRadaConnector:
    """РљРѕРЅРЅРµРєС‚РѕСЂ РґР»СЏ zakon.rada.gov.ua (Р†РџРЎ В«Р—Р°РєРѕРЅРѕРґР°РІСЃС‚РІРѕ РЈРєСЂР°С—Р»РµРЅРёВ»)."""

    def __init__(self) -> None:
        self.base_url = settings.ZAKON_RADA_BASE_URL.rstrip("/")
        self.rss_url = settings.ZAKON_RADA_RSS_URL
        self.timeout = settings.ZAKON_RADA_REQUEST_TIMEOUT
        self.max_retries = settings.ZAKON_RADA_MAX_RETRIES
        self._client = None
        self.parser = ZakonRadaParser(base_url=self.base_url)

    async def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": USER_AGENT}  # S3.3: ввічливий UA з контактом
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check_source(self):
        try:
            validate_url(self.rss_url, stage="request")  # S3.3
            rate_limiter.wait()
            client = await self._get_client()
            resp = await client.get(self.rss_url, follow_redirects=True)
            ct = resp.headers.get("content-type", "")
            record_source_result(self.rss_url, ok=resp.status_code < 400, error=None if resp.status_code < 400 else f"HTTP {resp.status_code}")
            return SourceCheck(
                reachable=resp.status_code < 400,
                status_code=resp.status_code,
                content_type=ct,
                note=(
                    "RSS endpoint reachable; returned HTML wrapper in this environment, "
                    "raw RSS-XML not confirmed as a stable public API."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            record_source_result(self.rss_url, ok=False, error=str(exc))
            return SourceCheck(
                reachable=False,
                status_code=None,
                content_type=None,
                note=f"Source unreachable: {exc!s}",
            )

    @staticmethod
    def _checksum(content):
        return hashlib.sha256(content).hexdigest()

    async def fetch_document_page(self, source_url):
        try:
            validate_url(source_url, stage="request")  # S3.3: білий список перед запитом
        except SourceNotAllowed as exc:
            log_source_not_allowed(source_url, stage="request")
            return {
                "source_url": source_url,
                "verified": False,
                "error": str(exc),
                "note": "URL відхилено білим списком джерел",
            }

        cached = get_cached_raw(source_url)  # S3.3: кеш сирих відповідей
        if cached is not None:
            content_sha, html, fetched_at = cached
            return {
                "source_url": source_url,
                "status_code": 200,
                "content_type": "text/html; charset=utf-8",
                "checksum": content_sha,
                "content_sha256": content_sha,
                "fetched_at": fetched_at,
                "raw_html": html,  # S3.5: повний HTML (обрізання ламало великі акти)
                "parser_version": "html-fetch-v1",
                "verified": True,
                "cached": True,
                "note": "Сторінку акта взято з кешу (повторний запит не качав мережу)",
            }

        client = await self._get_client()
        last_error = None
        for attempt in range(self.max_retries):
            try:
                rate_limiter.wait()  # S3.3: ≤1 запит/с
                resp = await client.get(source_url, follow_redirects=True)
                resp.raise_for_status()
                html = resp.text
                validate_url(source_url, stage="write")  # S3.3: перевірка перед записом
                content_sha, fetched_at = put_cached_raw(source_url, html)
                record_source_result(source_url, ok=True)
                return {
                    "source_url": source_url,
                    "status_code": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "checksum": content_sha,
                    "content_sha256": content_sha,
                    "fetched_at": fetched_at,
                    "raw_html": html,  # S3.5: повний HTML (обрізання ламало великі акти)
                    "parser_version": "html-fetch-v1",
                    "verified": True,
                    "note": "Завантажено сторінку акта з zakon.rada.gov.ua",
                }
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                record_source_result(source_url, ok=False, error=str(exc))
                await asyncio.sleep(2 ** attempt)
        return {
            "source_url": source_url,
            "verified": False,
            "error": last_error,
            "note": "Сторінку акта не вдалося завантажити після спроб",
        }

    async def parse_document(self, source_url):
        result = await self.fetch_document_page(source_url)
        if not result.get("verified"):
            return None

        html = result["raw_html"]
        try:
            parsed = self.parser.parse(html, source_url)
            return parsed
        except Exception as exc:
            import logging

            from app.services.import_stats import record_parse_error

            logging.getLogger("aiugoda.import").exception(
                "Помилка парсингу %s", source_url
            )
            record_parse_error(str(exc), source_url=source_url)
            return None

# S3.4 — Tier 1: 13 актів, nreg звірені з data.rada.gov.ua/doc.txt 05.11.2026 (docs/SOURCES_VERIFIED.md §6)
TIER1_URLS = [
        # S3.3: тексти статей — лише .frame (оболонка /laws/main/ не містить тексту)
        "https://zakon.rada.gov.ua/laws/show/254%D0%BA/96-%D0%B2%D1%80.frame",  # Конституція (254к/96-вр)
        "https://zakon.rada.gov.ua/laws/show/435-15.frame",   # Цивільний кодекс
        "https://zakon.rada.gov.ua/laws/show/436-15.frame",   # Господарський кодекс
        "https://zakon.rada.gov.ua/laws/show/2341-14.frame",  # Кримінальний кодекс
        "https://zakon.rada.gov.ua/laws/show/80731-10.frame", # КУпАП
        "https://zakon.rada.gov.ua/laws/show/2755-17.frame",  # Податковий кодекс
        "https://zakon.rada.gov.ua/laws/show/322-08.frame",   # Кодекс законів про працю
        "https://zakon.rada.gov.ua/laws/show/2947-14.frame",  # Сімейний кодекс
        "https://zakon.rada.gov.ua/laws/show/2768-14.frame",  # Земельний кодекс
        "https://zakon.rada.gov.ua/laws/show/4651-17.frame",  # Кримінальний процесуальний кодекс
        "https://zakon.rada.gov.ua/laws/show/1618-15.frame",  # Цивільний процесуальний кодекс
        "https://zakon.rada.gov.ua/laws/show/1798-12.frame",  # Господарський процесуальний кодекс
        "https://zakon.rada.gov.ua/laws/show/2747-15.frame",  # Кодекс адміністративного судочинства
]

# Блокування: одночасно лише один запуск імпорту (план S3, 3.3)
_import_lock = False


class ImportAlreadyRunning(Exception):
    """Імпорт уже запущено — другий запуск чекає або відхиляється (план S3, 3.7)."""


def import_locked() -> bool:
    return _import_lock


async def sync_once():
    """Фоновий імпорт Tier 1: 13 актів з zakon.rada.gov.ua.

    Повертає звіт: додано / оновлено / пропущено / помилок; пише import_run.
    """
    global _import_lock
    if _import_lock:
        raise ImportAlreadyRunning("імпорт уже запущено (блокування одного запуску)")

    from datetime import UTC, datetime

    from app.core.database import SessionLocal
    from app.models.import_run import ImportRun
    from app.models.legal_document import LegalDocument
    from app.services.import_service import ImportService
    from app.services.import_stats import parse_error_count, reset_parse_errors

    _import_lock = True
    db = SessionLocal()
    started = datetime.now(UTC)
    run = ImportRun(
        id=__import__("uuid").uuid4().hex,
        source="zakon.rada.gov.ua",
        status="running",
        started_at=started,
        created_at=started,
    )
    db.add(run)
    db.commit()

    import_service = ImportService(db)
    import_service.init_force_levels()

    stats = {"discovered": 0, "added": 0, "updated": 0, "skipped": 0, "errors": 0}
    failed: list[dict] = []
    reset_parse_errors()
    connector = ZakonRadaConnector()
    try:
        for url in TIER1_URLS:
            stats["discovered"] += 1
            try:
                parsed = await connector.parse_document(url)
                if parsed:
                    existed = (
                        db.query(LegalDocument)
                        .filter_by(source_id=parsed.source_id)
                        .first()
                        is not None
                    )
                    import_service.import_parsed_document(parsed)
                    if existed:
                        stats["updated"] += 1
                    else:
                        stats["added"] += 1
                else:
                    stats["errors"] += 1
                    failed.append({"url": url, "reason": "порожній або нечитабельний відповідь (розібрано 0)"})
            except Exception as exc:
                stats["errors"] += 1
                failed.append({"url": url, "reason": f"{type(exc).__name__}: {exc}"})
                import logging
                logging.getLogger("aiugoda.import").exception("Помилка імпорту %s", url)
                # S3: сесія після збої flush має бути відкочена, інакше
                # наступні URL та фінальний запис import_run теж падають.
                db.rollback()
    finally:
        await connector.close()
        if db.in_transaction():
            db.rollback()
        run_id = run.id
        from datetime import datetime as _dt

        fresh = db.get(
            __import__("app.models.import_run", fromlist=["ImportRun"]).ImportRun,
            run_id,
        )
        if fresh is not None:
            fresh.status = "finished"
            fresh.finished_at = datetime.now(UTC)
            fresh.added = stats["added"]
            fresh.updated = stats["updated"]
            fresh.skipped = stats["skipped"]
            fresh.errors = stats["errors"] + parse_error_count()
            from app.services.import_stats import warnings as collect_warnings

            fresh.report_json = {
                **stats,
                "parse_errors": parse_error_count(),
                "duration_sec": round((datetime.now(UTC) - started).total_seconds(), 1),
                "failed": failed,
                "warnings": collect_warnings(),
            }
            db.commit()
        db.close()
        _import_lock = False
        del _dt

    from app.services.import_stats import warnings as collected_warnings

    return {
        "source": "zakon.rada.gov.ua",
        "stats": stats,
        "parse_errors": parse_error_count(),
        "duration_sec": round((datetime.now(UTC) - started).total_seconds(), 1),
        "failed": failed,
        "warnings": collected_warnings(),
        "note": "Імпорт 13 актів Tier 1 (nreg звірені з doc.txt 05.11.2026)",
    }