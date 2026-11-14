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

import re
from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.conflict_candidate import ConflictCandidate
from app.models.document_revision import DocumentRevision
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
            winner = provision_a
            winner_doc, loser_doc = doc_a, doc_b
        elif priority_b < priority_a:
            winner = provision_b
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
            winner = provision_a
            winner_date, loser_date = rev_a_date, rev_b_date
            loser = provision_b
        else:
            winner = provision_b
            winner_date, loser_date = rev_b_date, rev_a_date
            loser = provision_a

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

    # ------------------------------------------------------------------
    # §6: чесні детектори за реальними даними (без попарного «кожен з кожним»)
    # ------------------------------------------------------------------

    _FULL_EXCL_RE = re.compile(
        r"\{\s*Статт[яюі]\s+(\d+(?:\s*-\s*\d+)?)\s+(?:на\s+підставі|виключен)",
        re.IGNORECASE,
    )
    _NOTE_RE = re.compile(r"\{([^{}]{5,1000})\}")
    _REF_THIS_ACT_RE = re.compile(
        r"статт[^\d\s]{0,4}\s+(\d+(?:\s*-\s*\d+)?)\s+[^.]{0,60}?цього\s+(?:Кодексу|Закону)",
        re.IGNORECASE,
    )
    _TEMP_NORM_RE = re.compile(
        r"на період дії воєнного стану|до закінчення терміну дії воєнного стану|"
        r"до (?:установлення|закінчення) особливого правового режиму",
        re.IGNORECASE,
    )

    @staticmethod
    def _norm_article(raw: str) -> str:
        return re.sub(r"\s*-\s*", "-", raw.strip())

    def detect_dead_references(self) -> list[ConflictCandidate]:
        """Відсилка на повністю виключену статтю того самого акта (DEAD_REFERENCE).

        Ллємо лише: (а) стаття повністю виключена приміткою джерела
        «{Статтю N виключено …}», (б) такої статті нема в розборі,
        (в) явна відсилка «статті N … цього Кодексу/Закону» поза примітками.
        Часткові виключення («частину статті N виключено») не рахуємо.
        """
        out: list[ConflictCandidate] = []
        docs = self.db.query(LegalDocument).filter(
            LegalDocument.data_origin == "official"
        ).all()
        for doc in docs:
            provisions = (
                self.db.query(LegalProvision)
                .join(
                    DocumentRevision,
                    DocumentRevision.id == LegalProvision.document_revision_id,
                )
                .filter(DocumentRevision.legal_document_id == doc.id)
                .all()
            )
            if not provisions:
                continue
            excluded: dict[str, str] = {}
            present: set[str] = set()
            for p in provisions:
                if p.article_number:
                    present.add(str(p.article_number))
                if p.text:
                    for m in self._FULL_EXCL_RE.finditer(p.text):
                        num = self._norm_article(m.group(1))
                        end = p.text.find("}", m.start())
                        note = p.text[m.start(): end + 1] if end != -1 else m.group(0)
                        excluded[num] = note.strip()[:300]
            if not excluded:
                continue
            for p in provisions:
                if not p.text:
                    continue
                stripped = self._NOTE_RE.sub(" ", p.text)
                for m in self._REF_THIS_ACT_RE.finditer(stripped):
                    num = self._norm_article(m.group(1))
                    if num not in excluded or num in present:
                        continue
                    ctx = stripped[max(0, m.start() - 100): m.end() + 80].strip()
                    out.append(
                        ConflictCandidate(
                            provision_a_id=p.id,
                            provision_b_id=p.id,
                            conflict_type="DEAD_REFERENCE",
                            evidence_json={
                                "reference_quote": ctx[:500],
                                "excluded_note": excluded[num],
                                "excluded_article": num,
                                "document": doc.title,
                            },
                            confidence="high",
                            review_status="Не підтверджено",
                            rule_applied=(
                                "Відсилка до статті, повністю виключеної з чинної "
                                "редакції цього самого акта"
                            ),
                            winner_provision_id=None,
                            explanation=(
                                f"«{doc.title}»: норма посилається на статтю {num}, яку "
                                f"джерело позначає виключеною: {excluded[num][:160]} "
                                "Норма-кандидат для перевірки експертом."
                            ),
                            source_of_detection="code",
                        )
                    )
        return out

    def detect_expiring_all(self) -> list[ConflictCandidate]:
        """Тимчасові норми з прямою умовою строку в тексті (EXPIRING)."""
        out: list[ConflictCandidate] = []
        rows = (
            self.db.query(LegalProvision, LegalDocument)
            .join(
                DocumentRevision,
                DocumentRevision.id == LegalProvision.document_revision_id,
            )
            .join(LegalDocument, LegalDocument.id == DocumentRevision.legal_document_id)
            .filter(LegalProvision.text.like("%воєнного стану%"))
            .limit(500)
            .all()
        )
        for prov, doc in rows:
            m = self._TEMP_NORM_RE.search(prov.text or "")
            if not m:
                continue
            cand = self.detect_expiring(prov, doc)
            if cand:
                cand.evidence_json = {
                    **(cand.evidence_json or {}),
                    "quote": m.group(0),
                    "provision_text_head": (prov.text or "")[:400],
                }
                cand.source_of_detection = "code"
                out.append(cand)
        return out

    def detect_code_duplications(self) -> list[ConflictCandidate]:
        """Дослівно однакові норми в різних актах (CODE_DUPLICATION).

        Лліво лише повний збіг SHA-256 тексту (>80 символів) між актами —
        це факт, а не схожість на погляд.
        """
        out: list[ConflictCandidate] = []
        dup_rows = (
            self.db.query(
                LegalProvision.content_checksum,
                func.count(func.distinct(DocumentRevision.legal_document_id)).label("n"),
            )
            .join(
                DocumentRevision,
                DocumentRevision.id == LegalProvision.document_revision_id,
            )
            .filter(
                LegalProvision.content_checksum.isnot(None),
                func.length(LegalProvision.text) > 80,
            )
            .group_by(LegalProvision.content_checksum)
            .having(func.count(func.distinct(DocumentRevision.legal_document_id)) > 1)
            .all()
        )
        for checksum, _n in dup_rows:
            provisions = (
                self.db.query(LegalProvision, LegalDocument)
                .join(
                    DocumentRevision,
                    DocumentRevision.id == LegalProvision.document_revision_id,
                )
                .join(LegalDocument, LegalDocument.id == DocumentRevision.legal_document_id)
                .filter(LegalProvision.content_checksum == checksum)
                .limit(10)
                .all()
            )
            if len(provisions) < 2:
                continue
            (prov_a, doc_a), (prov_b, doc_b) = provisions[0], provisions[1]
            if str(doc_a.id) == str(doc_b.id):
                continue
            out.append(
                ConflictCandidate(
                    provision_a_id=prov_a.id,
                    provision_b_id=prov_b.id,
                    conflict_type="CODE_DUPLICATION",
                    evidence_json={
                        "content_checksum": checksum,
                        "document_a": doc_a.title,
                        "document_b": doc_b.title,
                        "quote": (prov_a.text or "")[:500],
                        "quote_matches": True,
                    },
                    confidence="high",
                    review_status="Не підтверджено",
                    rule_applied="Дослівний збіг текстів норм у двох актах (SHA-256)",
                    winner_provision_id=None,
                    explanation=(
                        f"Норми актів «{doc_a.title}» ({prov_a.provision_identifier}) і "
                        f"«{doc_b.title}» ({prov_b.provision_identifier}) мають "
                        "дослівно однаковий текст (збіг SHA-256). Кандидат: можливе "
                        "дублювання або технічна помилка джерела; остаточно — експерт."
                    ),
                    source_of_detection="code",
                )
            )
        return out

    def run_all(self, persist: bool = True) -> list[ConflictCandidate]:
        """Запускає всі чесні детерміновані перевірки над даними БД.

        §6: без попарного «кожен акт × кожен акт» — лише правила за
        наявними фактами (відсилки на виключені статті, тимчасові норми,
        дослівні дублікати). Кандидати позначаються «Не підтверджено»
        до перевірки експертом.
        """
        candidates: list[ConflictCandidate] = []
        candidates += self.detect_dead_references()
        candidates += self.detect_expiring_all()
        candidates += self.detect_code_duplications()

        if not persist:
            return candidates

        # Дедуплікація: той самий тип + та сама пара норм — один кандидат
        # (унікальний індекс uq_conflict_candidates_pair).
        saved: list[ConflictCandidate] = []
        for cand in candidates:
            exists = (
                self.db.query(ConflictCandidate)
                .filter(
                    ConflictCandidate.provision_a_id == cand.provision_a_id,
                    ConflictCandidate.provision_b_id == cand.provision_b_id,
                    ConflictCandidate.conflict_type == cand.conflict_type,
                )
                .first()
            )
            if exists:
                saved.append(exists)
                continue
            self.db.add(cand)
            try:
                self.db.flush()
            except IntegrityError:
                self.db.rollback()
                continue
        self.db.commit()
        for cand in saved:
            self.db.refresh(cand)
        return saved or candidates

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
        except Exception:  # noqa: BLE001, S110 — lazy relationship: без revision значення лишається None
            pass  # nosec B110

        # §6: умова строку може бути прямо в тексті норми (не лише в метаданих):
        # «на період дії воєнного стану», «до закінчення терміну дії воєнного стану».
        text_condition = self._TEMP_NORM_RE.search(provision.text or "")

        if not is_temp and not valid_until and not effective_to and not text_condition:
            return None

        reasons = []
        if is_temp:
            reasons.append("позначено як тимчасова (is_temporary=True)")
        if valid_until:
            reasons.append("умова закінчення: " + str(valid_until))
        if effective_to:
            reasons.append("дата втрати чинності: " + str(effective_to))
        if text_condition:
            reasons.append("умова закінчення в тексті норми: «" + text_condition.group(0) + "»")

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