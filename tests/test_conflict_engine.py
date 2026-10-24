"""
Тести детектора колізій (ТЗ v2, розділ 3).
"""
from __future__ import annotations

import uuid
from datetime import date

from app.models.legal_document import LegalDocument
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision
from app.models.document_revision import DocumentRevision
from app.services.conflict_engine import ConflictEngine


def test_hierarchy_conflict_constitution_vs_code(svc) -> None:
    """Конституція (рівень 1) перемагає Кодекс (рівень 3)."""
    doc_const = svc.upsert_document(
        source_id="const-test",
        title="Конституція",
        document_type="Конституція",
        legal_force_level="constitution",
    )
    doc_code = svc.upsert_document(
        source_id="code-test",
        title="Кодекс",
        document_type="Кодекс",
        legal_force_level="code",
    )

    rev_const = svc.upsert_revision(document=doc_const, revision_label="R1", revision_date=date(1996, 6, 28))
    rev_code = svc.upsert_revision(document=doc_code, revision_label="R1", revision_date=date(2003, 1, 16))

    prov_const = svc.upsert_provision(
        revision=rev_const, provision_identifier="Стаття 3", article_number="3", text="Текст constitutions", ordinal=1
    )
    prov_code = svc.upsert_provision(
        revision=rev_code, provision_identifier="Стаття 6", article_number="6", text="Текст коду", ordinal=1
    )

    engine = ConflictEngine(svc.db)
    cand = engine.detect_hierarchy_conflict(prov_const, prov_code, doc_const, doc_code)

    assert cand is not None
    assert cand.conflict_type == "HIERARCHY_CONFLICT"
    assert cand.winner_provision_id == prov_const.id  # Конституція перемагає
    assert "lex superior" in cand.rule_applied


def test_same_level_newer(svc) -> None:
    """Дві норми одного рівня — побеждає новіша редакція."""
    doc_a = svc.upsert_document(
        source_id="law-a",
        title="Закон А",
        document_type="Закон",
        legal_force_level="law",
    )
    doc_b = svc.upsert_document(
        source_id="law-b",
        title="Закон Б",
        document_type="Закон",
        legal_force_level="law",
    )

    rev_a = svc.upsert_revision(document=doc_a, revision_label="R1", revision_date=date(2020, 1, 1))
    rev_b = svc.upsert_revision(document=doc_b, revision_label="R1", revision_date=date(2022, 1, 1))

    prov_a = svc.upsert_provision(
        revision=rev_a, provision_identifier="Стаття 5", article_number="5", text="Старий закон", ordinal=1
    )
    prov_b = svc.upsert_provision(
        revision=rev_b, provision_identifier="Стаття 5", article_number="5", text="Новий закон", ordinal=1
    )

    engine = ConflictEngine(svc.db)
    cand = engine.detect_same_level_newer(prov_a, prov_b, doc_a, doc_b, date(2020, 1, 1), date(2022, 1, 1))

    assert cand is not None
    assert cand.conflict_type == "SAME_LEVEL_NEWER"
    assert cand.winner_provision_id == prov_b.id  # Закон Б новийший
    assert "lex posterior" in cand.rule_applied


def test_dead_reference(svc) -> None:
    """Посилання на неіснуючиу статтю — DEAD_REFERENCE."""
    doc = svc.upsert_document(
        source_id="doc-with-link",
        title="Акт з посиланням",
        document_type="Закон",
    )
    rev = svc.upsert_revision(document=doc, revision_label="R1", revision_date=date(2021, 1, 1))
    prov = svc.upsert_provision(
        revision=rev, provision_identifier="Стаття 10", article_number="10", text="Посилання на Статью 999", ordinal=1
    )

    # Створюємо зв'язок на неіснуючий provision_id (без збереження в БД)
    link = LegalLink(
        source_provision_id=prov.id,
        link_type="refers_to",
        target_provision_id="00000000-0000-0000-0000-000000000999",
        evidence_text="Частина 1 статті 10 посилається на статтю 999",
    )

    engine = ConflictEngine(svc.db)
    cand = engine.detect_dead_reference(link)

    assert cand is not None
    assert cand.conflict_type == "DEAD_REFERENCE"
    assert cand.confidence == "high"
    assert cand.explanation is not None
    assert "неіснуючий" in cand.explanation