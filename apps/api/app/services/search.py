"""
Повнотекстовий пошук законодавства (TZ v2, розділ 8).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class SearchFilters:
    document_type: str | None = None
    status: str | None = None
    issuing_authority: str | None = None
    adoption_date_from: str | None = None
    adoption_date_to: str | None = None
    effective_date_from: str | None = None
    effective_date_to: str | None = None
    legal_force_level: str | None = None
    only_current: bool = True


@dataclass
class SearchResult:
    id: str
    source_id: str
    title: str
    document_type: str
    document_number: str | None
    adoption_date: str | None
    issuing_authority: str | None
    current_known_status: str | None
    source_url: str | None
    revision_id: str | None
    revision_date: str | None
    snippet: str | None
    matched_provision: str | None
    rank: float


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str, filters: SearchFilters | None = None, limit: int = 20, offset: int = 0):
        if filters is None:
            filters = SearchFilters()
        q = self._normalize(query)
        sql, params = self._sql(q, filters, limit, offset)
        rows = self.db.execute(text(sql), params).fetchall()
        cnt_sql, cnt_params = self._cnt_sql(q, filters)
        total = self.db.execute(text(cnt_sql), cnt_params).scalar() or 0
        res = []
        for row in rows:
            res.append(SearchResult(
                id=row.id, source_id=row.source_id, title=row.title,
                document_type=row.document_type, document_number=row.document_number,
                adoption_date=str(row.adoption_date) if row.adoption_date else None,
                issuing_authority=row.issuing_authority,
                current_known_status=row.current_known_status,
                source_url=row.source_url,
                revision_id=row.revision_id,
                revision_date=str(row.revision_date) if row.revision_date else None,
                snippet=row.snippet,
                matched_provision=row.matched_provision,
                rank=row.rank,
            ))
        return res, total

    def _normalize(self, q: str) -> str:
        q = re.sub(r"[^a-zA-Z0-9_\\s\"-]", " ", q, flags=re.UNICODE)
        q = re.sub(r"\s+", " ", q).strip()
        return q

    def _sql(self, q: str, filters: SearchFilters, limit: int, offset: int):
        base = "SELECT DISTINCT d.id, d.source_id, d.title, d.document_type, d.document_number, d.adoption_date, d.issuing_authority, d.current_known_status, d.source_url, r.id as revision_id, r.revision_date, r.normalized_text, p.provision_identifier, p.text as provision_text, substr(p.text, 1, 200) as snippet, NULL as matched_provision, 1.0 as rank FROM legal_documents d LEFT JOIN document_revisions r ON r.legal_document_id = d.id LEFT JOIN legal_provisions p ON p.document_revision_id = r.id"
        where = []
        params = {"limit": limit, "offset": offset}
        if filters.document_type:
            where.append("d.document_type = :document_type")
            params["document_type"] = filters.document_type
        if filters.status:
            where.append("d.current_known_status = :status")
            params["status"] = filters.status
        if filters.issuing_authority:
            where.append("d.issuing_authority = :issuing_authority")
            params["issuing_authority"] = filters.issuing_authority
        if filters.legal_force_level:
            where.append("d.legal_force_level = :legal_force_level")
            params["legal_force_level"] = filters.legal_force_level
        if filters.adoption_date_from:
            where.append("d.adoption_date >= :adoption_date_from")
            params["adoption_date_from"] = filters.adoption_date_from
        if filters.adoption_date_to:
            where.append("d.adoption_date <= :adoption_date_to")
            params["adoption_date_to"] = filters.adoption_date_to
        if filters.only_current:
            where.append("(r.effective_to IS NULL OR r.effective_to >= date('now'))")
        if q:
            where.append("(d.title LIKE :fts OR r.normalized_text LIKE :fts OR p.text LIKE :fts)")
            params["fts"] = f"%{q}%"
        where_sql = " WHERE " + " AND ".join(where) if where else ""
        return base + where_sql + " ORDER BY rank DESC, d.adoption_date DESC LIMIT :limit OFFSET :offset", params

    def _cnt_sql(self, q: str, filters: SearchFilters):
        base = "SELECT COUNT(DISTINCT d.id) FROM legal_documents d LEFT JOIN document_revisions r ON r.legal_document_id = d.id LEFT JOIN legal_provisions p ON p.document_revision_id = r.id"
        where = []
        params = {}
        if filters.document_type:
            where.append("d.document_type = :document_type")
            params["document_type"] = filters.document_type
        if filters.status:
            where.append("d.current_known_status = :status")
            params["status"] = filters.status
        if filters.issuing_authority:
            where.append("d.issuing_authority = :issuing_authority")
            params["issuing_authority"] = filters.issuing_authority
        if filters.legal_force_level:
            where.append("d.legal_force_level = :legal_force_level")
            params["legal_force_level"] = filters.legal_force_level
        if filters.adoption_date_from:
            where.append("d.adoption_date >= :adoption_date_from")
            params["adoption_date_from"] = filters.adoption_date_from
        if filters.adoption_date_to:
            where.append("d.adoption_date <= :adoption_date_to")
            params["adoption_date_to"] = filters.adoption_date_to
        if filters.only_current:
            where.append("(r.effective_to IS NULL OR r.effective_to >= date('now'))")
        if q:
            where.append("(d.title LIKE :fts OR r.normalized_text LIKE :fts OR p.text LIKE :fts)")
            params["fts"] = f"%{q}%"
        where_sql = " WHERE " + " AND ".join(where) if where else ""
        return base + where_sql, params

    def get_suggestions(self, partial: str, limit: int = 10):
        if len(partial) < 2:
            return []
        sql = "SELECT DISTINCT title FROM legal_documents WHERE title LIKE :partial ORDER BY title LIMIT :limit"
        rows = self.db.execute(text(sql), {"partial": f"%{partial}%", "limit": limit}).fetchall()
        return [row[0] for row in rows]

    def search_by_provision(self, provision_ref: str):
        match = re.search(r"(?:стаття|article)\s+(\d+[\w\-]*)", provision_ref, re.IGNORECASE)
        if not match:
            return []
        article_num = match.group(1)
        sql = """SELECT DISTINCT d.id, d.source_id, d.title, d.document_type, d.document_number, d.adoption_date, d.issuing_authority, d.current_known_status, d.source_url, r.id as revision_id, r.revision_date, p.provision_identifier, p.text as provision_text, 1.0 as rank FROM legal_documents d JOIN document_revisions r ON r.legal_document_id = d.id JOIN legal_provisions p ON p.document_revision_id = r.id WHERE p.article_number = :article_num ORDER BY d.adoption_date DESC NULLS LAST LIMIT 50"""
        rows = self.db.execute(text(sql), {"article_num": article_num}).fetchall()
        return [
            SearchResult(
                id=row.id, source_id=row.source_id, title=row.title,
                document_type=row.document_type, document_number=row.document_number,
                adoption_date=str(row.adoption_date) if row.adoption_date else None,
                issuing_authority=row.issuing_authority,
                current_known_status=row.current_known_status,
                source_url=row.source_url,
                revision_id=row.revision_id,
                revision_date=str(row.revision_date) if row.revision_date else None,
                snippet=None,
                matched_provision=f"Стаття {article_num}",
                rank=1.0,
            )
            for row in rows
        ]
