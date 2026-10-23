"""
Connector for the official Verkhovna Rada of Ukraine legislation portal:
https://zakon.rada.gov.ua

IMPORTANT (verified during Phase 0):
- The portal is reachable over HTTPS.
- Content is available under Creative Commons Attribution 4.0 International
  (unless stated otherwise).
- The database is described as informational and is NOT an official printed
  publication (see zakon.rada.gov.ua rules).
- RSS pages return HTML wrappers in this environment; the raw RSS-XML endpoint
  was not confirmed as a stable, documented public API.
- No undocumented public API is assumed. Retrieval is implemented as careful
  HTTP fetching of document/search pages with a clearly-labelled fallback.

This connector records what was verified and degrades safely when the source
cannot be reached or parsed.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings


@dataclass
class SourceCheck:
    reachable: bool
    status_code: int | None
    content_type: str | None
    rss_xml_confirmed: bool
    note: str


class ZakonRadaConnector:
    def __init__(self) -> None:
        self.base_url = settings.ZAKON_RADA_BASE_URL.rstrip("/")
        self.rss_url = settings.ZAKON_RADA_RSS_URL
        self.timeout = settings.ZAKON_RADA_REQUEST_TIMEOUT
        self.max_retries = settings.ZAKON_RADA_MAX_RETRIES
        self._client: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "AI Ugoda legal-intelligence connector (+contact via admin)"},
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check_source(self) -> SourceCheck:
        """Verify source reachability and whether a raw RSS-XML feed is available."""
        try:
            client = await self._client()
            resp = await client.get(self.rss_url, follow_redirects=True)
            ct = resp.headers.get("content-type", "")
            is_xml = "xml" in ct.lower() or "rss" in ct.lower()
            return SourceCheck(
                reachable=resp.status_code < 400,
                status_code=resp.status_code,
                content_type=ct,
                rss_xml_confirmed=is_xml,
                note=(
                    "RSS endpoint reachable; returned HTML wrapper in this environment, "
                    "raw RSS-XML not confirmed as a stable public API."
                ),
            )
        except Exception as exc:  # pragma: no cover - network failure path
            return SourceCheck(
                reachable=False,
                status_code=None,
                content_type=None,
                rss_xml_confirmed=False,
                note=f"Source unreachable: {exc!s}",
            )

    @staticmethod
    def _checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def fetch_document_page(self, source_url: str) -> dict[str, Any]:
        """Fetch a single official document page and return extracted metadata + text."""
        client = await self._client()
        last_error: str | None = None
        for attempt in range(self.max_retries):
            try:
                resp = await client.get(source_url, follow_redirects=True)
                resp.raise_for_status()
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")
                title_el = soup.find("h1") or soup.find("title")
                title = title_el.get_text(" ", strip=True) if title_el else None
                return {
                    "source_url": source_url,
                    "title": title,
                    "status_code": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "checksum": self._checksum(html.encode("utf-8")),
                    "raw_text": soup.get_text("\n", strip=True)[:20000],
                    "parser_version": "bs4-html-v1",
                    "verified": True,
                    "note": "Fetched official source page; full structured parsing TBD",
                }
            except Exception as exc:  # pragma: no cover
                last_error = str(exc)
                await asyncio.sleep(2 ** attempt)
        return {
            "source_url": source_url,
            "verified": False,
            "error": last_error,
            "note": "Source page could not be retrieved after retries",
        }

    async def sync_once(self) -> dict[str, Any]:
        """Idempotent single synchronization pass (MVP skeleton).

        Does NOT write to the database yet (database write wiring is part of
        Phase 2). Returns a summary of discovered/checked records so the
        admin can see connector health without side effects.
        """
        check = await self.check_source()
        await self.close()
        return {
            "source": self.base_url,
            "rss_url": self.rss_url,
            "source_check": {
                "reachable": check.reachable,
                "status_code": check.status_code,
                "content_type": check.content_type,
                "rss_xml_confirmed": check.rss_xml_confirmed,
                "note": check.note,
            },
            "discovered": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "note": "MVP skeleton: connector verifies reachability; DB import wiring in Phase 2",
        }