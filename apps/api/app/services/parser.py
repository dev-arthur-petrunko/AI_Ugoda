from __future__ import annotations  
  
import hashlib  
import re  
from dataclasses import dataclass, field  
from typing import Any  
  
from bs4 import BeautifulSoup 

@dataclass
class ProvisionNode:
    identifier: str
    level: str
    number: str
    title: str | None
    text: str
    parent_identifier: str | None = None
    children: list["ProvisionNode"] = field(default_factory=list)
    ordinal: int = 0
    content_checksum: str = ""

    def __post_init__(self):
        if not self.content_checksum:
            self.content_checksum = hashlib.sha256(
                (self.number + "|" + (self.title or "") + "|" + self.text).encode("utf-8")
            ).hexdigest()[:32]

@dataclass
class ParsedDocument:
    source_url: str
    source_id: str
    title: str
    document_type: str
    document_number: str | None
    adoption_date: str | None
    issuing_authority: str | None
    current_known_status: str | None
    nreg: str | None
    effective_date: str | None
    is_temporary: bool = False
    valid_until_condition: str | None = None
    provisions: list[ProvisionNode] = field(default_factory=list)
    raw_html_checksum: str = ""
    parser_version: str = "html-parser-v1"

class ZakonRadaParser:
    """Парсер HTML-сторінок zakon.rada.gov.ua."""

    SELECTORS = {
        "title": "h1.law-title, h1.title, .document-title h1",
        "meta_table": "table.law-meta, table.doc-info, .law-info table",
        "sections": "div.law-section, div.section, .document-body > div",
        "articles": "div.law-article, div.article, article",
        "parts": "div.law-part, div.part, p.part",
        "points": "div.law-point, div.point, p.point",
        "subpoints": "div.law-subpoint, div.subpoint, p.subpoint",
    }

    PATTERNS = {
        "article": re.compile(r"^\s*Стаття\s+(\d+[\w\-]*)", re.IGNORECASE),
        "part": re.compile(r"^\s*Частина\s+(перша|друга|третя|четверта|п'ята|шоста|сьома|восьма|дев'ята|десята|\d+)", re.IGNORECASE),
        "point": re.compile(r"^\s*Пункт\s+(\d+[\w\-]*)", re.IGNORECASE),
        "subpoint": re.compile(r"^\s*Підпункт\s+([\w\-]+)", re.IGNORECASE),
        "section": re.compile(r"^\s*Розділ\s+([IVXLC\d]+)", re.IGNORECASE),
        "chapter": re.compile(r"^\s*Глава\s+(\d+)", re.IGNORECASE),
    }

    def __init__(self, base_url: str = "https://zakon.rada.gov.ua"):
        self.base_url = base_url

    def parse(self, html: str, source_url: str) -> ParsedDocument:
        soup = BeautifulSoup(html, "html.parser")
        raw_checksum = hashlib.sha256(html.encode("utf-8")).hexdigest()

        title = self._extract_title(soup)
        meta = self._extract_metadata(soup, source_url)
        body = self._find_body_container(soup)
        provisions = self._parse_hierarchy(body, meta["source_id"])
        self._assign_ordinals(provisions)

        return ParsedDocument(
            source_url=source_url,
            source_id=meta["source_id"],
            title=title,
            document_type=meta["document_type"],
            document_number=meta["document_number"],
            adoption_date=meta["adoption_date"],
            issuing_authority=meta["issuing_authority"],
            current_known_status=meta["current_known_status"],
            nreg=meta["nreg"],
            effective_date=meta["effective_date"],
            is_temporary=meta["is_temporary"],
            valid_until_condition=meta["valid_until_condition"],
            provisions=provisions,
            raw_html_checksum=raw_checksum,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        for sel in ["h1.law-title", "h1.title", ".document-title h1", "h1"]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return "Без назви"

    def _extract_metadata(self, soup: BeautifulSoup, source_url: str) -> dict[str, Any]:
        meta = {
            "source_id": self._extract_source_id(source_url),
            "document_type": None,
            "document_number": None,
            "adoption_date": None,
            "issuing_authority": None,
            "current_known_status": None,
            "nreg": None,
            "effective_date": None,
            "is_temporary": False,
            "valid_until_condition": None,
        }

        for sel in ["table.law-meta", "table.doc-info", ".law-info table", "table"]:
            table = soup.select_one(sel)
            if table:
                self._parse_meta_table(table, meta)
                break

        nreg_match = re.search(r"/main/(\d+[-\w]*)", source_url)
        if nreg_match:
            meta["nreg"] = nreg_match.group(1)

        meta["document_type"] = self._infer_document_type(meta.get("title", ""))

        return meta

    def _extract_source_id(self, source_url: str) -> str:
        match = re.search(r"/main/([^/?#]+)", source_url)
        if match:
            slug = match.group(1).lower()
            slug = re.sub(r"[^\w\-]", "-", slug)
            slug = re.sub(r"-\+", "-", slug).strip("-")
            return slug[:100]
        return "unknown"

    def _parse_meta_table(self, table: BeautifulSoup, meta: dict) -> None:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)

                if "тип" in key or "вид" in key:
                    meta["document_type"] = val
                elif "номер" in key and "реєстрац" not in key:
                    meta["document_number"] = val
                elif "дата прийнят" in key or "утворен" in key:
                    meta["adoption_date"] = self._normalize_date(val)
                elif "орган" in key or "видав" in key:
                    meta["issuing_authority"] = val
                elif "статус" in key or "стан" in key:
                    meta["current_known_status"] = val
                elif "реєстрац" in key and "номер" in key:
                    meta["nreg"] = val
                elif "вступ" in key and "силу" in key:
                    meta["effective_date"] = self._normalize_date(val)

    def _normalize_date(self, date_str: str) -> str | None:
        if not date_str:
            return None
        patterns = [
            (r"(\d{2})\.(\d{2})\.(\d{4})", lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
            (r"(\d{4})-(\d{2})-(\d{2})", lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
            (r"(\d{1,2})\s+(\w+)\s+(\d{4})", self._parse_ukrainian_date),
        ]
        for pattern, formatter in patterns:
            m = re.search(pattern, date_str)
            if m:
                try:
                    return formatter(m)
                except Exception:
                    continue
        return None

    def _parse_ukrainian_date(self, match) -> str:
        months = {
            "січня": "01", "лютого": "02", "березня": "03", "квітня": "04",
            "травня": "05", "червня": "06", "липня": "07", "серпня": "08",
            "вересня": "09", "жовтня": "10", "листопада": "11", "грудня": "12",
        }
        day = int(match.group(1))
        month = months.get(match.group(2).lower(), "01")
        year = match.group(3)
        return f"{year}-{month}-{day:02d}"

    def _infer_document_type(self, title: str) -> str:
        title_lower = title.lower()
        if "конституц" in title_lower:
            return "Конституція"
        elif "кодекс" in title_lower:
            return "Кодекс"
        elif "закон" in title_lower and "проект" not in title_lower:
            return "Закон"
        elif "постанова" in title_lower and "кабінет" in title_lower:
            return "Постанова КМУ"
        elif "постанова" in title_lower and "верховн" in title_lower:
            return "Постанова ВР"
        elif "указ" in title_lower and "президент" in title_lower:
            return "Указ Президента"
        elif "наказ" in title_lower:
            return "Наказ"
        return "Інший акт"

    def _find_body_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        for sel in [
            ".law-body", ".document-body", ".law-text",
            "div.law-content", "div.document-content",
            "main", "article", ".content"
        ]:
            container = soup.select_one(sel)
            if container:
                return container
        return soup

    def _parse_hierarchy(self, container: BeautifulSoup, act_id: str) -> list[ProvisionNode]:
        provisions = []
        current_section = None
        current_article = None
        current_part = None
        current_point = None
        current_subpoint = None
        ordinal = 0

        elements = container.find_all(["div", "p", "h2", "h3", "h4", "h5", "span", "li"])

        for el in elements:
            text = el.get_text(" ", strip=True)
            if not text or len(text) < 3:
                continue

            ordinal += 1
            level, number, title, clean_text = self._classify_element(text)

            if not level:
                if current_subpoint:
                    current_subpoint.text += " " + clean_text
                elif current_point:
                    current_point.text += " " + clean_text
                elif current_part:
                    current_part.text += " " + clean_text
                elif current_article:
                    current_article.text += " " + clean_text
                elif current_section:
                    current_section.text += " " + clean_text
                continue

            identifier = f"{act_id}/{level}/{number}"
            if level == "part" and current_article:
                identifier = f"{act_id}/article/{current_article.number}/part/{number}"
            elif level == "point" and current_part:
                identifier = f"{act_id}/article/{current_article.number}/part/{current_part.number}/point/{number}"
            elif level == "subpoint" and current_point:
                identifier = f"{act_id}/article/{current_article.number}/part/{current_part.number}/point/{current_point.number}/subpoint/{number}"

            node = ProvisionNode(
                identifier=identifier,
                level=level,
                number=number,
                title=title,
                text=clean_text,
                ordinal=ordinal,
            )

            if level == "section":
                node.parent_identifier = None
                provisions.append(node)
                current_section = node
                current_article = current_part = current_point = current_subpoint = None
            elif level == "article":
                node.parent_identifier = current_section.identifier if current_section else None
                if current_section:
                    current_section.children.append(node)
                else:
                    provisions.append(node)
                current_article = node
                current_part = current_point = current_subpoint = None
            elif level == "part":
                node.parent_identifier = current_article.identifier if current_article else (current_section.identifier if current_section else None)
                if current_article:
                    current_article.children.append(node)
                elif current_section:
                    current_section.children.append(node)
                else:
                    provisions.append(node)
                current_part = node
                current_point = current_subpoint = None
            elif level == "point":
                node.parent_identifier = current_part.identifier if current_part else (current_article.identifier if current_article else None)
                if current_part:
                    current_part.children.append(node)
                elif current_article:
                    current_article.children.append(node)
                else:
                    provisions.append(node)
                current_point = node
                current_subpoint = None
            elif level == "subpoint":
                node.parent_identifier = current_point.identifier if current_point else None
                if current_point:
                    current_point.children.append(node)
                else:
                    provisions.append(node)
                current_subpoint = node

        return provisions

    def _classify_element(self, text: str) -> tuple[str | None, str | None, str | None, str]:
        text_stripped = text.strip()

        for level, pattern in self.PATTERNS.items():
            match = pattern.match(text_stripped)
            if match:
                number = match.group(1)
                title_end = match.end()
                title = text_stripped[title_end:].strip(" .:-")
                clean_text = text_stripped
                return level, number, title if title else None, clean_text

        return None, None, None, text_stripped

    def _assign_ordinals(self, provisions: list[ProvisionNode], parent_ordinal: int = 0) -> int:
        ordinal = parent_ordinal
        for node in provisions:
            ordinal += 1
            node.ordinal = ordinal
            if node.children:
                ordinal = self._assign_ordinals(node.children, ordinal)
        return ordinal


REFERENCE_PATTERNS = [
    re.compile(r"(?:згідно|відповідно|в установі|на підставі|за статтею|за частиною|за пунктом)\s+(?:до\s+)?(?:статті|частини|пункту)\s+(\d+[\w\-]*)\s+(?:Закону|Кодексу|Постанови|Указу|Наказу)\s+(?:України\s+)?[\"«]([^\"»]+)[\"»]", re.IGNORECASE),
    re.compile(r"(?:стаття|частина|пункт)\s+(\d+[\w\-]*)\s+(?:Закону|Кодексу|Постанови|Указу|Наказу)\s+(?:України\s+)?[\"«]([^\"»]+)[\"»]", re.IGNORECASE),
    re.compile(r"[\"«]([^\"»]+)[\"»].*(?:стаття|частина|пункт)\s+(\d+[\w\-]*)", re.IGNORECASE),
]


def extract_references(text: str, source_provision_id: str) -> list[dict[str, Any]]:
    """Витягує посилання на інші нормативні акти з тексту."""
    references = []
    for pattern in REFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            target_provision = match.group(1)
            target_act_title = match.group(2) if len(match.groups()) > 1 else ""
            references.append({
                "source_provision_id": source_provision_id,
                "target_provision_identifier": target_provision,
                "target_act_title": target_act_title,
                "reference_type": "refers_to",
                "evidence_text": match.group(0)[:500],
                "resolution_status": "pending",
            })
    return references
