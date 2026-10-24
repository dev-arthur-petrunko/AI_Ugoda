"""
Детектор колізій (ТЗ v3, розділ B.6).

Детермінований движок правил колізій:
- HIERARCHY_CONFLICT — акт нижчого рівня юридичної сили противичить вищому (lex superior)
- SPECIAL_VS_GENERAL — дві норми одного рівня, одна 특殊на, інша загальна
- SAME_LEVEL_NEWER — однаковий рівень, побеждає новіша редакція (lex posterior)
- DEAD_REFERENCE — посилання на акт/статтю, яких немає в базі
- GHOST_NORM — закон вимагає прийняти підзаконний акт/порядок, але такого акта не існує
- UNCONSTITUTIONAL — Конституційний Суд визнав норму неконституційною (лише за записом у constitutional_decision)
- EXPIRING — тимчасова норма з датою або умовою закінчення дії (напр. «на час воєнного стану»)
- CODE_DUPLICATION — однакові норми в різних кодексах/законах
- EU_MISMATCH — розходження з директивою ЄС (етап 3)

Результат — ConflictCandidate зі статусом candidate (потребує людської перевірки).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models.conflict_candidate import ConflictCandidate
from app.models.legal_document import LegalDocument
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision


class ConflictEngine:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _force_priority(self, document: LegalDocument) -> int:
        """Повертає пріоритет рівня юридичної сили (чише число = вищий рівень)."""
        level = document.legal_force_level or "code"
        mapping = {
            "constitution": 1,
            "treaty": 2,
            "code": 3,
            "law": 3,
            "parliament_resolution": 4,
            "presidential_decree": 5,
            "cabinet_resolution": 6,
            "minister_order": 7,
            "local_act": 8,
        }
        return mapping.get(level, 3)

    def detect_hierarchy_conflict(
        self,
        provision_a: LegalProvision,
        provision_b: LegalProvision,
        doc_a: LegalDocument,
        doc_b: LegalDocument,
    ) -> ConflictCandidate | None:
        """
        Якщо акт B має нижчий рівень сили, ніж акт A, і вони регулюють одну тему —
        це можлива HIERARCHY_CONFLICT. Побігає акт A (вищий рівень).
        """
        priority_a = self._force_priority(doc_a)
        priority_b = self._force_priority(doc_b)

        if priority_a < priority_b:
            winner, loser = provision_a, provision_b
            winner_doc, loser_doc = doc_a, doc_b
        elif priority_b < priority_a:
            winner, loser = provision_b, provision_a
            winner_doc, loser_doc = doc_b, doc_a
        else:
            return None  # однаковий рівень — не hierarchy конфікт

        return ConflictCandidate(
            provision_a_id=provision_a.id,
            provision_b_id=provision_b.id,
            conflict_type="HIERARCHY_CONFLICT",
            evidence_json={
                "provision_a": {
                    "identifier": provision_a.provision_identifier,
                    "document": doc_a.title,
                    "force_level": doc_a.legal_force_level,
                },
                "provision_b": {
                    "identifier": provision_b.provision_identifier,
                    "document": doc_b.title,
                    "force_level": doc_b.legal_force_level,
                },
            },
            confidence="medium",
            review_status="Не підтверджено",
            rule_applied="lex superior (вищий рівень юридичної сили перемагає)",
            winner_provision_id=winner.id,
            explanation=(
                f"Акт «{winner_doc.title}» (рівень {winner_doc.legal_force_level}) "
                f"має вищий юридичний аніст, ніж «{loser_doc.title}» ({loser_doc.legal_force_level}). "
                f"Норма вищого рівня перемагає."
            ),
        )

    def detect_same_level_newer(
        self,
        provision_a: LegalProvision,
        provision_b: LegalProvision,
        doc_a: LegalDocument,
        doc_b: LegalDocument,
        rev_a_date: date | None,
        rev_b_date: date | None,
    ) -> ConflictCandidate | None:
        """
        Дві норми одного рівняsilи. Побеждає новіша редакція (lex posterior).
        """
        if not rev_a_date or not rev_b_date:
            return None
        if rev_a_date == rev_b_date:
            return None

        if rev_a_date > rev_b_date:
            winner, loser = provision_a, provision_b
            winner_date, loser_date = rev_a_date, rev_b_date
        else:
            winner, loser = provision_b, provision_a
            winner_date, loser_date = rev_b_date, rev_a_date

        return ConflictCandidate(
            provision_a_id=provision_a.id,
            provision_b_id=provision_b.id,
            conflict_type="SAME_LEVEL_NEWER",
            evidence_json={
                "provision_a": {
                    "identifier": provision_a.provision_identifier,
                    "revision_date": rev_a_date.isoformat() if rev_a_date else None,
                },
                "provision_b": {
                    "identifier": provision_b.provision_identifier,
                    "revision_date": rev_b_date.isoformat() if rev_b_date else None,
                },
            },
            confidence="high",
            review_status="Не підтверджено",
            rule_applied="lex posterior (новиший закон перемагає старіший на одному рівні)",
            winner_provision_id=winner.id,
            explanation=(
                f"Норма «{winner.provision_identifier}» ({winner_date.isoformat()}) "
                f"новиша за «{loser.provision_identifier}» ({loser_date.isoformat()}). "
                f"На одному рівні юридичної сили перемагає новіша редакція."
            ),
        )

    def detect_dead_reference(
        self,
        link: LegalLink,
    ) -> ConflictCandidate | None:
        """
        Посилання на акт/статтю, яких немає в базі (DEAD_REFERENCE).
        """
        if link.target_provision_id is None and link.target_document_id is None:
            return None

        Provision = __import__("app.models.legal_provision", fromlist=["LegalProvision"]).LegalProvision

        target_exists = False
        if link.target_provision_id:
            target_exists = (
                self.db.query(Provision).filter_by(id=link.target_provision_id).first()
            ) is not None
        if link.target_document_id:
            target_exists = (
                self.db.query(LegalDocument).filter_by(id=link.target_document_id).first()
            ) is not None

        if not target_exists:
            source_prov = (
                self.db.query(Provision).filter_by(id=link.source_provision_id).first()
            )
            source_name = source_prov.provision_identifier if source_prov else "невідомо"
            return ConflictCandidate(
                provision_a_id=link.source_provision_id,
                provision_b_id=link.source_provision_id,
                conflict_type="DEAD_REFERENCE",
                evidence_json={
                    "link_type": link.link_type,
                    "evidence_text": link.evidence_text,
                    "target_provision_id": str(link.target_provision_id) if link.target_provision_id else None,
                    "target_document_id": str(link.target_document_id) if link.target_document_id else None,
                },
                confidence="high",
                review_status="Не підтверджено",
                rule_applied="Посилання веде на неіснуючий акт або статтю",
                winner_provision_id=None,
                explanation=(
                    f"Посилання {link.link_type} з пункту «{source_name}» "
                    f"веде на неіснуючий акт/статтю (місце в никуда)."
                ),
            )
        return None

    def run_all(self) -> list[ConflictCandidate]:
        """
        Запускає всі детерміновані перевірки над існуючими даними в БД.
        Повертає список знайдених кандидатів (без запису в БД — викликач вирішує).
        """
        candidates: list[ConflictCandidate] = []

        docs = self.db.query(LegalDocument).all()
        Provision = __import__("app.models.legal_provision", fromlist=["LegalProvision"]).LegalProvision
        provisions = self.db.query(Provision).all()
        links = self.db.query(LegalLink).all()

        revision_ids_by_doc = {
            d.id: [r.id for r in d.revisions] for d in docs
        }
        for i, doc_a in enumerate(docs):
            for doc_b in docs[i + 1 :]:
                provs_a = [p for p in provisions if p.document_revision_id in revision_ids_by_doc.get(doc_a.id, [])]
                provs_b = [p for p in provisions if p.document_revision_id in revision_ids_by_doc.get(doc_b.id, [])]
                if provs_a and provs_b:
                    c = self.detect_hierarchy_conflict(provs_a[0], provs_b[0], doc_a, doc_b)
                    if c:
                        candidates.append(c)

        for link in links:
            c = self.detect_dead_reference(link)
            if c:
                candidates.append(c)

        return candidates

    def detect_expiring(
        self,
        provision: LegalProvision,
        document: LegalDocument,
    ) -> ConflictCandidate | None:
        """
        Тимчасова норма з датою або умовою закінчення дії (EXPIRING).
        Наприклад: «на період дії воєнного стану».
        """
        is_temp = getattr(document, 'is_temporary', False)
        valid_until = getattr(document, 'valid_until_condition', None)
        effective_to = None
        try:
            rev = provision.revision
            if rev:
                effective_to = rev.effective_to
        except Exception:
            pass

        if not is_temp and not valid_until and not effective_to:
            return None

        reasons = []
        if is_temp:
            reasons.append("позначено як тимчасова (is_temporary=True)")
        if valid_until:
            reasons.append("умова закінчення: " + str(valid_until))
        if effective_to:
            reasons.append("дата втрати чинності: " + str(effective_to))

        return ConflictCandidate(
            provision_a_id=provision.id,
            provision_b_id=provision.id,
            conflict_type="EXPIRING",
            evidence_json={
                "document_title": document.title,
                "is_temporary": is_temp,
                "valid_until_condition": valid_until,
                "effective_to": str(effective_to) if effective_to else None,
                "reasons": reasons,
            },
            confidence="high",
            review_status="Не підтверджено",
            rule_applied="Тимчасова норма з датою/умовою закінчення дії",
            winner_provision_id=None,
            explanation=(
                "Норма акта \u00ab" + document.title + "\u00bb є тимчасовою: " + ", ".join(reasons) + ". "
                "Після закінчення терміну норма втрачає чинність."
            ),
        )

    def detect_ghost_norm(
        self,
        provision: LegalProvision,
        document: LegalDocument,
        required_act_description: str,
    ) -> ConflictCandidate | None:
        """
        Закон вимагає прийняти підзаконний акт/порядок, але такого акта не існує (GHOST_NORM).
        required_act_description — опис того, що закон вимагає прийняти.
        """
        return ConflictCandidate(
            provision_a_id=provision.id,
            provision_b_id=provision.id,
            conflict_type="GHOST_NORM",
            evidence_json={
                "document_title": document.title,
                "provision_identifier": provision.provision_identifier,
                "required_act_description": required_act_description,
            },
            confidence="medium",
            review_status="Не підтверджено",
            rule_applied="Закон вимагає прийняти акт, якого немає в базі",
            winner_provision_id=None,
            explanation=(
                "Акт \u00ab" + document.title + "\u00bb (норма \u00ab" + provision.provision_identifier + "\u00bb) "
                "вимагає прийняти: " + required_act_description + ". Такого акта не знайдено."
            ),
        )