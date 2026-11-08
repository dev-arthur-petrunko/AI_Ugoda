"""
Тести S3.7 — стійкість імпорту та дублі.

- Повторний імпорт: added 0, пропущено N (ідемпотентність).
- Той самий текст під іншою датою → нова редакція НЕ створюється (UNIQUE
  (document_id, effective_from) + ідемпотентний upsert за змістом).
- Два імпорти одночасно → другий відхиляється блокуванням (ImportAlreadyRunning).
"""
from __future__ import annotations

from datetime import date

from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument


def _import_once(svc, source_id: str, effective_from: date, text: str) -> int:
    """Один повний прохід імпорту; повертає кількість ДОДАНИХ документів."""
    svc.upsert_force_level(level=3, name="Закон", priority_weight=80)
    existed = (
        svc.db.query(LegalDocument)
        .filter(LegalDocument.source_id == source_id)
        .first()
        is not None
    )
    doc = svc.upsert_document(
        source_id=source_id,
        title="Тестовий акт S3",
        document_type="Закон",
        document_number="1-TEST",
        nreg="1-TEST",
        adoption_date=date(2024, 1, 1),
        issuing_authority="Верховна Рада України",
        legal_force_level="law",
        current_known_status="Чинний",
        source_url="https://zakon.rada.gov.ua/laws/main/1-test",
    )
    rev = svc.upsert_revision(
        document=doc,
        revision_label="Редакція 1",
        revision_date=effective_from,
        effective_from=effective_from,
        effective_to=None,
        normalized_text=text,
        source_url="https://zakon.rada.gov.ua/laws/main/1-test",
        verification_status="verified",
    )
    svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 1",
        article_number="1",
        heading="Заголовок статті 1",
        text=text,
        ordinal=1,
    )
    return 0 if existed else 1


def test_reimport_added_0(svc) -> None:
    """S3.7: другий запуск імпорту — added 0, документів не більшає."""
    added1 = _import_once(svc, "s3-act-reimport", date(2024, 1, 1), "Текст статті 1.")
    assert added1 == 1

    total_before = svc.db.query(LegalDocument).count()
    added2 = _import_once(svc, "s3-act-reimport", date(2024, 1, 1), "Текст статті 1.")
    total_after = svc.db.query(LegalDocument).count()

    assert added2 == 0, f"повторний імпорт має додати 0, отримано {added2}"
    assert total_after == total_before, "документів не має бути більше після повторного імпорту"


def test_same_text_different_date_no_new_revision(svc) -> None:
    """S3.7: той самий текст під іншою датою → нова редакція не створюється."""
    text = "Текст статті 1 (той самий)."
    _import_once(svc, "s3-act-redating", date(2024, 1, 1), text)
    doc = (
        svc.db.query(LegalDocument)
        .filter(LegalDocument.source_id == "s3-act-redating")
        .one()
    )
    revisions_before = (
        svc.db.query(DocumentRevision)
        .filter(DocumentRevision.legal_document_id == doc.id)
        .count()
    )

    # Повторний імпорт того самого тексту, але з іншою датою редакції
    _import_once(svc, "s3-act-redating", date(2025, 6, 15), text)
    svc.db.expire_all()

    revisions_after = (
        svc.db.query(DocumentRevision)
        .filter(DocumentRevision.legal_document_id == doc.id)
        .count()
    )
    assert (
        revisions_after == revisions_before
    ), f"нова редакція не має створюватись: було {revisions_before}, стало {revisions_after}"

    # S3.7: лише попередження — воно має бути зараховане (не «тихе»).
    from app.services.import_stats import warning_count

    assert warning_count() >= 1, "попередження про той самий текст під іншою датою має бути зараховане"


def test_import_lock_rejects_second_run() -> None:
    """S3.7: два імпорти одночасно → другий відхиляється (блокування)."""
    import asyncio

    # Симуляція: перший запуск утримує блокування
    import app.services.connector as conn
    from app.services.connector import ImportAlreadyRunning, import_locked

    conn._import_lock = True
    try:
        assert import_locked() is True

        async def _second_run():
            await conn.sync_once()

        loop = asyncio.new_event_loop()
        try:
            raised = False
            try:
                loop.run_until_complete(_second_run())
            except ImportAlreadyRunning:
                raised = True
            assert raised, "другий запуск мав бути відхилений блокуванням"
        finally:
            loop.close()
    finally:
        conn._import_lock = False
