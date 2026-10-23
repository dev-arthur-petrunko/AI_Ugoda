"""
Коннектори офіційних джерел законодавства України (ТЗ v2, розділ 1).
https://zakon.rada.gov.ua

Пріоритет джерел:
1. data.rada.gov.ua — відкриті дані ВР (CSV/JSON/XML, оновлення щогодини).
2. zakon.rada.gov.ua — ІПС «Законодавство Україлені» (запасне, HTML).

Правило: парсинг HTML — лише запасний варіант. Перед написанням коннектора агент
обов'язково перевіряє вручну, що адреса відповідає, формат збігається і які є ліміти,
і записує результат в docs/SOURCES_VERIFIED.md.

Єдине правило проєкту: ніколи не вигадуємо закон. Джерела не знайдено — пишемо
«не знайдено в базі».
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class SourceCheck:
    reachable: bool
    status_code: int | None
    content_type: str | None
    note: str



class DataRadaConnector:
    """Коннектор для data.rada.gov.ua — відкриті дані законодавства ВР."""

    def __init__(self) -> None:
        self.base_url = settings.DATA_RADA_BASE_URL.rstrip("/")
        self.laws_list_url = settings.DATA_RADA_LAWS_LIST_URL
        self.timeout = settings.DATA_RADA_REQUEST_TIMEOUT
        self.max_retries = settings.DATA_RADA_MAX_RETRIES
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
        """Перевіряє досяжність data.rada.gov.ua/ogd/zak/laws/list.json."""
        try:
            client = await self._client()
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
        except Exception as exc:  # pragma: no cover - network failure path
            return SourceCheck(
                reachable=False,
                status_code=None,
                content_type=None,
                note=f"data.rada.gov.ua unreachable: {exc!s}",
            )

    async def fetch_laws_list(self) -> dict[str, Any]:
        """Отримує індекс набору даних законів (list.json). Повертає сыру відповідь."""
        client = await self._client()
        last_error: str | None = None
        for attempt in range(self.max_retries):
            try:
                resp = await client.get(self.laws_list_url, follow_redirects=True)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "source_url": self.laws_list_url,
                    "status_code": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "checksum": _checksum(resp.content),
                    "data": data,
                    "verified": True,
                    "note": "Отримано індекс набору законів з data.rada.gov.ua",
                }
            except Exception as exc:  # pragma: no cover
                last_error = str(exc)
                await asyncio.sleep(2 ** attempt)
        return {
            "source_url": self.laws_list_url,
            "verified": False,
            "error": last_error,
            "note": "Не вдалося отримати індекс законів з data.rada.gov.ua після спроб",
        }



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
        """Перевіряє досяжність zakon.rada.gov.ua і чистого RSS-XML."""
        try:
            client = await self._client()
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
        except Exception as exc:  # pragma: no cover - network failure path
            return SourceCheck(
                reachable=False,
                status_code=None,
                content_type=None,
                note=f"Source unreachable: {exc!s}",
            )

    @staticmethod
    def _checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def fetch_document_page(self, source_url: str) -> dict[str, Any]:
        """Завантажує сторінку окремого акта з zakon.rada.gov.ua (запасне джерело)."""
        client = await self._client()
        last_error: str | None = None
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
                    "note": "Завантажено сторінку акта з zakon.rada.gov.ua; структурний парсинг TBD",
                }
            except Exception as exc:  # pragma: no cover
                last_error = str(exc)
                await asyncio.sleep(2 ** attempt)
        return {
            "source_url": source_url,
            "verified": False,
            "error": last_error,
            "note": "Сторінку акта не вдалося завантажити після спроб",
        }


        """Одиночна синхронізація (скелет MVP). Не пише в БД без побічних ефектів."""
        check = await self.check_source()
        await self.close()
        return {
            "source": self.base_url,
            "rss_url": self.rss_url,
            "source_check": {
                "reachable": check.reachable,
                "status_code": check.status_code,
                "content_type": check.content_type,
                "note": check.note,
            },
            "discovered": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "note": "MVP skeleton: коннектор перевіряє досяжність; імпорт у БД — на Фазі 2",
        }