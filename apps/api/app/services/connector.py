"""
РљРѕРЅРЅРµРєС‚РѕСЂРё РѕС„С–С†С–Р№РЅРёС… РґР¶РµСЂРµР» Р·Р°РєРѕРЅРѕРґР°РІСЃС‚РІР° РЈРєСЂР°С—РЅРё (РўР— v2, СЂРѕР·РґС–Р» 1).
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass

from app.core.config import settings
from app.services.parser import ZakonRadaParser


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
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check_source(self):
        try:
            client = await self._get_client()
            resp = await client.get(self.laws_list_url, follow_redirects=True)
            ct = resp.headers.get("content-type", "")
            is_json = "json" in ct.lower()
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
            return SourceCheck(
                reachable=False,
                status_code=None,
                content_type=None,
                note=f"data.rada.gov.ua unreachable: {exc!s}",
            )

    async def fetch_laws_list(self):
        client = await self._get_client()
        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = await client.get(self.laws_list_url, follow_redirects=True)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "source_url": self.laws_list_url,
                    "status_code": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "data": data,
                    "verified": True,
                }
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
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
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check_source(self):
        try:
            client = await self._get_client()
            resp = await client.get(self.rss_url, follow_redirects=True)
            ct = resp.headers.get("content-type", "")
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
        client = await self._get_client()
        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = await client.get(source_url, follow_redirects=True)
                resp.raise_for_status()
                html = resp.text
                return {
                    "source_url": source_url,
                    "status_code": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "checksum": self._checksum(html.encode("utf-8")),
                    "raw_html": html[:200000],
                    "parser_version": "html-fetch-v1",
                    "verified": True,
                    "note": "Р—Р°РІР°РЅС‚Р°Р¶РµРЅРѕ СЃС‚РѕСЂС–РЅРєСѓ Р°РєС‚Р° Р· zakon.rada.gov.ua",
                }
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                await asyncio.sleep(2 ** attempt)
        return {
            "source_url": source_url,
            "verified": False,
            "error": last_error,
            "note": "РЎС‚РѕСЂС–РЅРєСѓ Р°РєС‚Р° РЅРµ РІРґР°Р»РѕСЃСЏ Р·Р°РІР°РЅС‚Р°Р¶РёС‚Рё РїС–СЃР»СЏ СЃРїСЂРѕР±",
        }

    async def parse_document(self, source_url):
        result = await self.fetch_document_page(source_url)
        if not result.get("verified"):
            return None

        html = result["raw_html"]
        try:
            parsed = self.parser.parse(html, source_url)
            return parsed
        except Exception as exc:  # noqa: BLE001
            print(f"Parser error for {source_url}: {exc}")
            return None

async def sync_once():
    from app.core.database import SessionLocal
    from app.services.import_service import ImportService

    db = SessionLocal()
    import_service = ImportService(db)

    import_service.init_force_levels()

    test_urls = [
        "https://zakon.rada.gov.ua/laws/main/254%D0%BA/96-%D0%B2%D1%80",
        "https://zakon.rada.gov.ua/laws/main/435-15",
        "https://zakon.rada.gov.ua/laws/main/2341-14",
        "https://zakon.rada.gov.ua/laws/main/807-20",
        "https://zakon.rada.gov.ua/laws/main/2755-17",
    ]

    connector = ZakonRadaConnector()
    stats = {"discovered": 0, "imported": 0, "updated": 0, "skipped": 0, "failed": 0}

    for url in test_urls:
        stats["discovered"] += 1
        try:
            parsed = await connector.parse_document(url)
            if parsed:
                import_service.import_parsed_document(parsed)
                stats["imported"] += 1
                print(f"вњ“ Imported: {parsed.title}")
            else:
                stats["failed"] += 1
                print(f"вњ— Failed to parse: {url}")
        except Exception as exc:  # noqa: BLE001
            stats["failed"] += 1
            print(f"вњ— Error importing {url}: {exc}")
        await asyncio.sleep(1)

    await connector.close()
    db.close()

    return {
        "source": "zakon.rada.gov.ua",
        "stats": stats,
        "note": "Р†РјРїРѕСЂС‚ 5 С‚РµСЃС‚РѕРІРёС… Р°РєС‚С–РІ С‡РµСЂРµР· HTML-РїР°СЂСЃРёРЅРі",
    }