"""FTS Ukrainian morphology tests (Stage 6).

Run against a real PostgreSQL instance with Hunspell dictionaries installed
(Docker stack). Skipped automatically on SQLite (default unit-test env).
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from app.services.search import SearchService
from app.models.legal_document import LegalDocument
from app.models.document_revision import DocumentRevision
from app.models.legal_provision import LegalProvision


def _is_postgres(db) -> bool:
    try:
        return db.get_bind().dialect.name == "postgresql"
    except Exception:
        return False




def test_fts_config_and_dictionary(db) -> None:
    if not _is_postgres(db):
        pytest.skip("PostgreSQL required")
    row = db.execute(text("SELECT 1 FROM pg_ts_config WHERE cfgname = 'ukrainian'")).fetchone()
    assert row is not None, "ukrainian text search config missing"
    lex = db.execute(text("SELECT ts_lexize('ukrainian_hunspell', 'закони')")).scalar()
    assert lex is not None
    assert "закон" in [str(x) for x in (lex or [])], f"lemmatization failed: {lex}"


def test_fts_search_match(db) -> None:
    if not _is_postgres(db):
        pytest.skip("PostgreSQL required")
    doc = LegalDocument(source_id="fts-doc", title="Тестовий закон про морфологію", document_type="Закон")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    rev = DocumentRevision(legal_document_id=doc.id, effective_from=None, normalized_text="Текст про закони України.")
    db.add(rev)
    db.commit()
    db.refresh(rev)
    prov = LegalProvision(
        document_revision_id=rev.id,
        provision_identifier="Стаття 1",
        text="Українські закони регулюють суспільні відносини.",
    )
    db.add(prov)
    db.commit()

    svc = SearchService(db)
    results, total = svc.search("закон")
    assert total >= 1, "FTS search should match 'закон' against 'закони/законами'"
    assert any("морфолог" in (r.title or "") or "закон" in (r.title or "").lower() for r in results)
