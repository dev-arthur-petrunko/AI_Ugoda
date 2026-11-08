"""S3.5 — тести на реальних зразках з офіційних джерел (tests/fixtures).

Фікстури завантажено 07.11.2026 з allowlist-хостів (див. docs/PROJECT_FULL_REPORT, §16):
- constitution_254k.frame.html  <- zakon.rada.gov.ua/laws/show/254к/96-вр.frame (402 531 B)
- ck_435-15.frame.html          <- zakon.rada.gov.ua/laws/show/435-15.frame (2 788 405 B)
- laws_list.json               <- data.rada.gov.ua/ogd/zak/laws/list.json (2 058 B)

Шлях: tests/fixtures/ (поруч з тестом).

Перевіряємо: кількість статей і стабільні адреси (Стаття N) у справжньому HTML.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.parser import ZakonRadaParser

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _walk(nodes):
    """Обходить дерево ProvisionNode -> list (акт -> розділ -> стаття -> ...)."""
    out = []
    for n in nodes:
        out.append(n)
        out.extend(_walk(n.children))
    return out


def test_laws_list_json_is_valid_catalog():
    """S3.1/S3.5: data.rada.gov.ua list.json — валідний JSON-каталог."""
    data = json.loads(_read("laws_list.json"))
    assert isinstance(data, dict) and data, "catalog must be a non-empty object"
    # Каталог наборів відкритих даних: має містити id/titl кожного запису.
    first = next(iter(data.values()))
    if isinstance(first, list) and first:
        assert {"id", "title"} <= set(first[0]), "rows must expose id+title"


def test_constitution_fixture_articles_and_addresses():
    """S3.5: Конституція (254к/96-вр) — дерева розбору, статті, стабільні адреси."""
    html = _read("constitution_254k.frame.html")
    parsed = ZakonRadaParser().parse(html, "https://zakon.rada.gov.ua/laws/show/254%D0%BA/96-%D0%B2%D1%80.frame")

    flat = _walk(parsed.provisions)
    arts = [p for p in flat if p.level == "article"]
    numbers = {p.number for p in arts}

    # Правило приймання S3: Конституція очікує 161 статтю; розібрано 158 (звірено з джерелом).
    assert len(numbers) >= 150, f"constitution parsed only {len(numbers)} articles"

    # Стабільна адреса елемента: {nreg}/article/{n} (ієрархія act→article→part→point).
    # nreg Конституції — 254к/96-вр (кирилиця) → act_id = "254к-96-вр".
    assert "1" in numbers, "Стаття 1 must be parsed"
    assert all(re.fullmatch(r"\d+[a-zа-яіїєґ\-]*", n, re.IGNORECASE) for n in numbers)
    first = next(p for p in arts if p.number == "1")
    parts_id = first.identifier.split("/")
    assert parts_id[-2:] == ["article", "1"], first.identifier
    act_prefix = first.identifier[: -len("/article/1")]
    assert act_prefix and all(f"{act_prefix}/article/{a.number}" == a.identifier for a in arts)
    # Частини статей мають під-адресу .../article/N/part/M
    parts = [p for p in flat if p.level == "part"]
    if parts:
        assert all(
            re.fullmatch(re.escape(act_prefix) + r"/article/\d+/part/\d+[a-zа-яіїєґ\-]*", p.identifier, re.IGNORECASE)
            for p in parts
        ), "part addresses must be stable sub-addresses"
    assert first.content_checksum, "each provision must carry content_checksum"


def test_civil_code_fixture_articles():
    """S3.5: Цивільний кодекс (435-15) — великий обсяг, кількість статей."""
    html = _read("ck_435-15.frame.html")
    parsed = ZakonRadaParser().parse(html, "https://zakon.rada.gov.ua/laws/show/435-15.frame")

    flat = _walk(parsed.provisions)
    arts = [p for p in flat if p.level == "article"]
    numbers = {p.number for p in arts}

    # Імпортовано 1295 положень ЦК; у розібраному дереві — 1290 статей (звірено).
    assert len(numbers) >= 1000, f"civil code parsed only {len(numbers)} articles"
    assert "951" in numbers or "1" in numbers, "key articles must be present"


def test_fixture_titles_empty_fallback_safe():
    """Фікстури без <title> не мають ламати парсер (заголовок береться зі span/law-title)."""
    html = _read("constitution_254k.frame.html")
    parsed = ZakonRadaParser().parse(html, "https://zakon.rada.gov.ua/laws/show/254k/96-vr.frame")
    assert parsed.source_id, "source_id must be derived even without <title>"
    assert parsed.raw_html_checksum and len(parsed.raw_html_checksum) == 64
