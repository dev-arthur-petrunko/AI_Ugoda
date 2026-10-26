"""
Тести сервісу імпорту (ТЗ v2, розділ 2 — конвеєр ingest).
Перевіряє ідемпотентність upsert і контрольні суми.
"""
from __future__ import annotations

from datetime import date

from app.models.legal_document import LegalDocument
from app.models.legal_force_level import LegalForceLevel


def test_upsert_force_level_creates_and_is_idempotent(svc) -> None:
    lvl = svc.upsert_force_level(level=1, name="Конституція", description="Найвичий рівень", priority_weight=100)
    assert lvl.level == 1
    assert lvl.name == "Конституція"
    assert lvl.priority_weight == 100

    # Повторний виклик — оновлює, не дублює
    lvl2 = svc.upsert_force_level(level=1, name="Конституція оновлена", priority_weight=110)
    assert lvl2.id == lvl.id
    assert lvl2.name == "Конституція оновлена"
    assert lvl2.priority_weight == 110

    count = svc.db.query(LegalForceLevel).filter(LegalForceLevel.level == 1).count()
    assert count == 1


def test_upsert_document_creates_and_is_idempotent(svc) -> None:
    svc.upsert_force_level(level=3, name="Кодекс", priority_weight=80)

    doc = svc.upsert_document(
        source_id="test-act-001",
        title="Тестовий кодекс",
        document_type="Кодекс",
        document_number="123-IV",
        nreg="123-IV",
        adoption_date=date(2020, 1, 1),
        issuing_authority="Верховна Рада України",
        legal_force_level="code",
        current_known_status="Чинний",
        source_url="https://example.org/act/123",
        source_metadata_json={"foo": "bar"},
    )
    assert doc.source_id == "test-act-001"
    assert doc.title == "Тестовий кодекс"
    assert doc.nreg == "123-IV"

    # Повторний виклик з тим же source_id — оновлює, не дублює
    doc2 = svc.upsert_document(
        source_id="test-act-001",
        title="Тестовий кодекс оновлений",
    )
    assert doc2.id == doc.id
    assert doc2.title == "Тестовий кодекс оновлений"

def test_upsert_revision_and_provision(svc) -> None:
    doc = svc.upsert_document(
        source_id="test-act-002",
        title="Тестовий акт для ревізії",
        document_type="Закон",
    )

    rev = svc.upsert_revision(
        document=doc,
        revision_label="Редакція 1",
        revision_date=date(2021, 1, 1),
        effective_from=date(2021, 1, 1),
        effective_to=None,
        normalized_text="Текст положення статті 1.",
        source_url="https://example.org/act/002/rev1",
        verification_status="verified",
    )
    assert rev.legal_document_id == doc.id
    assert rev.effective_from == date(2021, 1, 1)
    assert rev.source_hash != ""  # хеш нормалізованого тексту
    assert rev.source_checksum != ""  # контрольна сумма сирого вмісту

    prov = svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 1",
        article_number="1",
        heading="Заголовок статті 1",
        text="Текст положення статті 1.",
        ordinal=1,
    )
    assert prov.document_revision_id == rev.id
    assert prov.article_number == "1"
    assert prov.content_checksum != ""

def test_upsert_provision_idempotent_by_natural_key(svc) -> None:
    """Повторний upsert з тим же provision_identifier оновлює існуючий запис (idempotent)."""
    doc = svc.upsert_document(
        source_id="test-act-002",
        title="Тестовий акт для ревізії",
        document_type="Закон",
    )

    rev = svc.upsert_revision(
        document=doc,
        revision_label="Редакція 1",
        revision_date=date(2021, 1, 1),
        effective_from=date(2021, 1, 1),
        effective_to=None,
        normalized_text="Текст положення статті 1.",
        source_url="https://example.org/act/002/rev1",
        verification_status="verified",
    )

    prov = svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 1",
        article_number="1",
        heading="Заголовок статті 1",
        text="Текст положення статті 1.",
        ordinal=1,
    )
    assert prov.document_revision_id == rev.id
    assert prov.article_number == "1"
    assert prov.content_checksum != ""

    # Повторний upsert з тим же provision_identifier оновлює існуючий запис (idempotent)
    prov2 = svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 1",
        article_number="1",
        heading="Заголовок статті 1 оновлений",
        text="Текст положення статті 1 оновлений.",
        ordinal=1,
    )
    assert prov2.id == prov.id


def test_act_n_provisions_to_db(svc) -> None:
    """Акт з N статтями має дати рівно N записів у legal_provisions (без дублів)."""
    N = 7
    doc = svc.upsert_document(
        source_id=f"test-act-n-{N}",
        title=f"Тестовий акт з {N} статтями",
        document_type="Закон",
    )
    rev = svc.upsert_revision(
        document=doc,
        revision_label="Редакція 1",
        revision_date=date(2021, 1, 1),
        effective_from=date(2021, 1, 1),
        effective_to=None,
        normalized_text="\n\n".join(f"Текст статті {i}." for i in range(1, N + 1)),
        source_url=f"https://example.org/act/n/{N}/rev1",
        verification_status="verified",
    )
    for i in range(1, N + 1):
        svc.upsert_provision(
            revision=rev,
            provision_identifier=f"Стаття {i}",
            article_number=str(i),
            heading=f"Заголовок статті {i}",
            text=f"Текст статті {i}.",
            ordinal=i,
        )
    count = svc.db.query(__import__("app.models.legal_provision", fromlist=["LegalProvision"]).LegalProvision).filter(
        __import__("app.models.legal_provision", fromlist=["LegalProvision"]).LegalProvision.document_revision_id == rev.id
    ).count()
    assert count == N, f"очікувалося {N} статей, отримано {count}"