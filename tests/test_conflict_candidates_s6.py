"""§6: чесні кандидати колізій — відсилки на виключені статті, тимчасові норми,
дослівні дублікати. Без попарного «кожен акт × кожен акт»."""

from __future__ import annotations

from datetime import date

from app.services.conflict_engine import ConflictEngine


def test_dead_reference_to_excluded_article(svc) -> None:
    """Відсилка «статті N цього Кодексу», де N повністю виключено — кандидат."""
    doc = svc.upsert_document(
        source_id="code-dead",
        title="Тестовий кодекс",
        document_type="Кодекс",
        legal_force_level="code",
        data_origin="official",
    )
    rev = svc.upsert_revision(document=doc, revision_label="R1", revision_date=date(2020, 1, 1))
    # Примітка виключення лежить у тілі сусідньої статті (не окремим рядом 147 —
    # як у джерелі: виключена стаття не має рядка в розборі).
    svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 146",
        article_number="146",
        text="{Статтю 147 виключено на підставі Закону № 1234-VI від 01.01.2020 }",
        ordinal=1,
    )
    svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 137",
        article_number="137",
        text="Порядок визначається статтею 147 цього Кодексу.",
        ordinal=2,
    )

    engine = ConflictEngine(svc.db)
    cands = engine.detect_dead_references()
    assert len(cands) == 1
    c = cands[0]
    assert c.conflict_type == "DEAD_REFERENCE"
    assert c.confidence == "high"
    assert c.review_status == "Не підтверджено"
    assert c.source_of_detection == "code"
    assert "147" in c.evidence_json["excluded_article"]
    assert "цього Кодексу" in c.evidence_json["reference_quote"]


def test_partial_exclusion_is_not_dead_reference(svc) -> None:
    """Часткове виключення («частину статті виключено») — не кандидат."""
    doc = svc.upsert_document(
        source_id="code-partial",
        title="Кодекс (часткове)",
        document_type="Кодекс",
        legal_force_level="code",
        data_origin="official",
    )
    rev = svc.upsert_revision(document=doc, revision_label="R1", revision_date=date(2020, 1, 1))
    svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 10",
        article_number="10",
        text="{Частину третю статті 10 виключено на підставі Закону № 99-VI від 01.01.2010 }",
        ordinal=1,
    )
    svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 11",
        article_number="11",
        text="Дивіться статтю 10 цього Кодексу.",
        ordinal=2,
    )

    engine = ConflictEngine(svc.db)
    assert engine.detect_dead_references() == []


def test_expiring_temporary_norm(svc) -> None:
    """Тимчасова норма з прямою умовою в тексті — EXPIRING з цитатою."""
    doc = svc.upsert_document(
        source_id="law-temp",
        title="Закон (воєнний стан)",
        document_type="Закон",
        legal_force_level="law",
        data_origin="official",
    )
    rev = svc.upsert_revision(document=doc, revision_label="R1", revision_date=date(2022, 1, 1))
    prov = svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 5",
        article_number="5",
        text="Пільга діє на період дії воєнного стану.",
        ordinal=1,
    )

    engine = ConflictEngine(svc.db)
    cands = engine.detect_expiring_all()
    assert len(cands) == 1
    c = cands[0]
    assert c.conflict_type == "EXPIRING"
    assert c.provision_a_id == prov.id
    assert "воєнного стану" in c.evidence_json["quote"]
    assert c.review_status == "Не підтверджено"


def test_code_duplication_exact_hash(svc) -> None:
    """Дослівний збіг SHA-256 двох норм різних актів — CODE_DUPLICATION."""
    doc_a = svc.upsert_document(
        source_id="dup-a",
        title="Акт А",
        document_type="Закон",
        legal_force_level="law",
        data_origin="official",
    )
    doc_b = svc.upsert_document(
        source_id="dup-b",
        title="Акт Б",
        document_type="Закон",
        legal_force_level="law",
        data_origin="official",
    )
    text = "Текст норми, ідентичної в двох актах. " * 5  # >80 символів
    rev_a = svc.upsert_revision(document=doc_a, revision_label="R1", revision_date=date(2020, 1, 1))
    rev_b = svc.upsert_revision(document=doc_b, revision_label="R1", revision_date=date(2021, 1, 1))
    svc.upsert_provision(revision=rev_a, provision_identifier="Стаття 3", article_number="3", text=text, ordinal=1)
    svc.upsert_provision(revision=rev_b, provision_identifier="Стаття 7", article_number="7", text=text, ordinal=1)

    engine = ConflictEngine(svc.db)
    cands = engine.detect_code_duplications()
    assert len(cands) == 1
    c = cands[0]
    assert c.conflict_type == "CODE_DUPLICATION"
    assert c.evidence_json["quote_matches"] is True
    assert c.confidence == "high"


def test_run_all_persists_idempotently(svc) -> None:
    """run_all(persist=True) зберігає кандидатів; повтор не дублює (UNIQUE)."""
    doc = svc.upsert_document(
        source_id="run-doc",
        title="Акт для run_all",
        document_type="Закон",
        legal_force_level="law",
        data_origin="official",
    )
    rev = svc.upsert_revision(document=doc, revision_label="R1", revision_date=date(2020, 1, 1))
    svc.upsert_provision(
        revision=rev,
        provision_identifier="Стаття 5",
        article_number="5",
        text="Пільга діє на період дії воєнного стану.",
        ordinal=1,
    )

    engine = ConflictEngine(svc.db)
    first = engine.run_all(persist=True)
    second = engine.run_all(persist=True)
    # Обидва прогони повертають ті самі збережені кандидати без дублікатів.
    ids_first = {str(c.id) for c in first}
    ids_second = {str(c.id) for c in second}
    assert ids_first == ids_second
    assert len(ids_first) >= 1

    from app.models.conflict_candidate import ConflictCandidate

    total = svc.db.query(ConflictCandidate).count()
    assert total == len(ids_first)
