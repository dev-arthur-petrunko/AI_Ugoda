"""
Сервіс імпорту актів законодавства (ТЗ v2, розділ 2 — конвеєр ingest).

Реалізує ідемпотентний імпорт:
- LegalDocument + DocumentRevision + LegalProvision
- Збереження raw_payload, контрольних сум SHA-256
- Редакції з effective_from / effective_to
- Жодних вигаданих даних: лише реальні публічні метадані актів
"""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_event import LegalEvent
from app.models.legal_force_level import LegalForceLevel
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision
from app.services.change_notes import extract_change_notes
from app.services.parser import ParsedDocument


def _checksum(content: bytes | str | dict | None) -> str:
    if content is None:
        content = ""
    if isinstance(content, dict):
        import json
        content = json.dumps(content, sort_keys=True, ensure_ascii=False)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _host_of(url: str | None) -> str | None:
    """S3.3: хост джерела для document_revisions.source_host."""
    if not url:
        return None
    from urllib.parse import urlparse
    return (urlparse(url).hostname or "").lower() or None


class ImportService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db or SessionLocal()

    def __enter__(self) -> ImportService:  # noqa: PYI034
        return self

    def init_force_levels(self) -> None:
        """Ініціалізує рівні юридичної сили за ТЗ v2."""
        levels = [
            (1, "Конституція України", "Найвища правова сила", 100),
            (2, "Міжнародні договори", "Згода на обов'язковість дала ВР", 90),
            (3, "Закони та Кодекси", "Законодавча влада", 80),
            (4, "Постанови Верховної Ради", "Акти ВР", 70),
            (5, "Укази Президента", "Президентські декрети", 60),
            (6, "Постанови КМУ", "Виконавча влада", 50),
            (7, "Накази міністерств", "Міністерства та відомства", 40),
            (8, "Місцеві акти", "Органи місцевого самоврядування", 30),
        ]
        for level, name, desc, weight in levels:
            self.upsert_force_level(level, name, desc, weight)

    def upsert_force_level(
        self, level: int, name: str, description: str | None = None, priority_weight: int = 0
    ) -> LegalForceLevel:
        row = (
            self.db.query(LegalForceLevel)
            .filter(LegalForceLevel.level == level)
            .first()
        )
        if row:
            row.name = name
            row.description = description
            row.priority_weight = priority_weight
            self.db.commit()
            self.db.refresh(row)
            return row
        row = LegalForceLevel(
            level=level,
            name=name,
            description=description,
            priority_weight=priority_weight,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def upsert_document(
        self,
        *,
        source_id: str,
        title: str,
        document_type: str | None = None,
        document_number: str | None = None,
        nreg: str | None = None,
        adoption_date: date | None = None,
        issuing_authority: str | None = None,
        legal_force_level: str | None = None,
        current_known_status: str = "Статус потребує перевірки",
        source_url: str | None = None,
        source_metadata_json: dict | None = None,
        is_temporary: bool = False,
        valid_until_condition: str | None = None,
        data_origin: str = "fixture",
    ) -> LegalDocument:
        row = (
            self.db.query(LegalDocument)
            .filter(LegalDocument.source_id == source_id)
            .first()
        )
        # S3.4: офіційний імпорт може зійтись із фікстурою за nreg
        # (уникальний індекс uq_legal_documents_nreg) — «приймаємо» рядок фікстури
        # і переводимо його в official, а не створюємо дублікат.
        # Порівняння без урахування регістру: 254к/96-вр vs 254к/96-ВР.
        if row is None and nreg:
            row = (
                self.db.query(LegalDocument)
                .filter(func.lower(LegalDocument.nreg) == nreg.lower())
                .first()
            )
        if row:
            row.source_id = source_id  # офіційний імпорт перетягує фікстурний source_id
            row.title = title
            row.document_type = document_type
            row.document_number = document_number
            row.nreg = nreg
            row.adoption_date = adoption_date
            row.issuing_authority = issuing_authority
            row.legal_force_level = legal_force_level
            row.current_known_status = current_known_status
            row.source_url = source_url
            row.source_metadata_json = source_metadata_json or {}
            row.is_temporary = is_temporary
            row.valid_until_condition = valid_until_condition
            row.data_origin = data_origin
            self.db.commit()
            self.db.refresh(row)
            return row
        row = LegalDocument(
            source_id=source_id,
            title=title,
            document_type=document_type,
            document_number=document_number,
            nreg=nreg,
            adoption_date=adoption_date,
            issuing_authority=issuing_authority,
            legal_force_level=legal_force_level,
            current_known_status=current_known_status,
            source_url=source_url,
            source_metadata_json=source_metadata_json or {},
            is_temporary=is_temporary,
            valid_until_condition=valid_until_condition,
            data_origin=data_origin,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def __exit__(self, *args: object) -> None:
        self.db.close()

    def upsert_revision(
        self,
        *,
        document: LegalDocument,
        revision_label: str | None = None,
        revision_date: date | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        source_url: str | None = None,
        raw_payload: str | None = None,
        normalized_text: str | None = None,
        parser_version: str = "html-fetch-v1",
        imported_at: date | None = None,
        verification_status: str = "unverified",
    ) -> DocumentRevision:
        row = None
        if effective_from is not None:
            row = (
                self.db.query(DocumentRevision)
                .filter(
                    DocumentRevision.legal_document_id == document.id,
                    DocumentRevision.effective_from == effective_from,
                )
                .first()
            )
        # Also check by source_hash to handle re-imports with same content
        if row is None and normalized_text is not None:
            computed_hash = _checksum(normalized_text)
            row = (
                self.db.query(DocumentRevision)
                .filter(
                    DocumentRevision.legal_document_id == document.id,
                    DocumentRevision.source_hash == computed_hash,
                )
                .first()
            )
        # S3.7: той самий текст під іншою датою → нова редакція НЕ створюється,
        # лише попередження (не «тихе»: лічиться та логиться).
        if (
            row is not None
            and normalized_text
            and row.source_hash == _checksum(normalized_text)
            and effective_from is not None
            and row.effective_from != effective_from
        ):
            from app.services.import_stats import record_warning

            record_warning(
                "Той самий текст (SHA-256 збігається) запропоновано з іншою датою "
                f"({row.effective_from} -> {effective_from}): нову редакцію не створено",
                source_url=source_url,
                document_id=str(document.id),
            )
        if row:
            row.revision_label = revision_label
            row.revision_date = revision_date
            row.effective_to = effective_to
            row.source_url = source_url
            row.source_host = _host_of(source_url)  # S3.3
            row.source_checksum = _checksum(raw_payload or "")
            row.source_hash = _checksum(normalized_text or "")
            row.original_content_location = source_url
            row.normalized_text = normalized_text
            row.parser_version = parser_version
            row.imported_at = imported_at
            row.verification_status = verification_status
            self.db.commit()
            self.db.refresh(row)
            return row
        row = DocumentRevision(
            legal_document_id=document.id,
            revision_label=revision_label,
            revision_date=revision_date,
            effective_from=effective_from,
            effective_to=effective_to,
            source_url=source_url,
            source_host=_host_of(source_url),  # S3.3
            source_checksum=_checksum(raw_payload or ""),
            source_hash=_checksum(normalized_text or ""),
            original_content_location=source_url,
            normalized_text=normalized_text,
            parser_version=parser_version,
            imported_at=imported_at,
            verification_status=verification_status,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def upsert_provision(
        self,
        *,
        revision: DocumentRevision,
        provision_identifier: str,
        article_number: str | None = None,
        part_number: str | None = None,
        point_number: str | None = None,
        subpoint_number: str | None = None,
        heading: str | None = None,
        text: str | None = None,
        ordinal: int | None = None,
        parent_provision_id: str | None = None,
    ) -> LegalProvision:
        row = (
            self.db.query(LegalProvision)
            .filter(
                LegalProvision.document_revision_id == revision.id,
                LegalProvision.provision_identifier == provision_identifier,
            )
            .first()
        )
        if row:
            row.article_number = article_number
            row.part_number = part_number
            row.point_number = point_number
            row.subpoint_number = subpoint_number
            row.heading = heading[:500] if heading else heading  # S3.5: ліміт VARCHAR(500)
            row.text = text
            row.ordinal = ordinal
            row.parent_provision_id = parent_provision_id
            row.content_checksum = _checksum(text or "")
            self.db.commit()
            self.db.refresh(row)
            return row
        row = LegalProvision(
            document_revision_id=revision.id,
            provision_identifier=provision_identifier[:100],
            article_number=article_number,
            part_number=part_number,
            point_number=point_number,
            subpoint_number=subpoint_number,
            heading=heading[:500] if heading else heading,  # S3.5: ліміт VARCHAR(500)
            text=text,
            ordinal=ordinal,
            parent_provision_id=parent_provision_id,
            content_checksum=_checksum(text or ""),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def create_link(
        self,
        *,
        source_provision: LegalProvision,
        target_provision: LegalProvision | None = None,
        target_document: LegalDocument | None = None,
        link_type: str = "refers_to",
        direction: str = "source_to_target",
        evidence_text: str | None = None,
        resolution_status: str = "unresolved",
    ) -> LegalLink:
        row = LegalLink(
            source_provision_id=source_provision.id,
            target_provision_id=target_provision.id if target_provision else None,
            target_document_id=target_document.id if target_document else None,
            link_type=link_type,
            direction=direction,
            evidence_text=evidence_text,
            resolution_status=resolution_status,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def import_parsed_document(self, parsed: ParsedDocument) -> LegalDocument:
        """Імпортує повний розпарсений документ з ParsedDocument."""
        # 1. Визначаємо рівень юридичної сили
        force_level = self._map_document_type_to_force_level(parsed.document_type)

        # 2. Створюємо/оновлюємо документ
        doc = self.upsert_document(
            source_id=parsed.source_id,
            title=parsed.title,
            document_type=parsed.document_type,
            document_number=parsed.document_number,
            nreg=parsed.nreg,
            adoption_date=parsed.adoption_date,
            issuing_authority=parsed.issuing_authority,
            legal_force_level=force_level,
            current_known_status=parsed.current_known_status or "Статус потребує перевірки",
            source_url=parsed.source_url,
            source_metadata_json={"parser_version": parsed.parser_version},
            is_temporary=parsed.is_temporary,
            valid_until_condition=parsed.valid_until_condition,
            data_origin="official",  # S3.2: реальний імпорт з джерела
        )

        # 3. Створюємо редакцію
        effective_from = None
        if parsed.effective_date:
            try:
                effective_from = date.fromisoformat(parsed.effective_date)
            except Exception:  # noqa: BLE001, S110 — биті дати з джерела: effective_from лишається None
                pass  # nosec B110

        # Об'єднуємо всі положення в нормалізований текст
        all_text = self._flatten_provisions_text(parsed.provisions)
        raw_payload = {
            "source_url": parsed.source_url,
            "source_id": parsed.source_id,
            "parser_version": parsed.parser_version,
            "raw_html_checksum": parsed.raw_html_checksum,
            "provisions_count": len(self._collect_all_provisions(parsed.provisions)),
        }

        revision = self.upsert_revision(
            document=doc,
            revision_label="Оригінал",
            revision_date=effective_from or parsed.adoption_date,
            effective_from=effective_from,
            effective_to=None,
            source_url=parsed.source_url,
            raw_payload=raw_payload,
            normalized_text=all_text,
            parser_version=parsed.parser_version,
            imported_at=datetime.now(UTC),
            verification_status="parsed",
        )

        # 4. Імпортуємо положення рекурсивно
        self._import_provisions_recursive(revision, parsed.provisions)

        # 5. §4.3: з офіційних приміток про зміни будуємо legal_links + legal_events
        self.build_links_for_revision(revision, doc)

        return doc

    def build_links_for_revision(
        self, revision: DocumentRevision, document: LegalDocument
    ) -> dict[str, int]:
        """§4.3: ідемпотентно будує зв'язки й події з приміток джерела.

        Джерело фактів — офіційні примітки у фігурних дужках:
        «{Статтю 65 доповнено … згідно із Законом № 3587-IX від 22.02.2024}».
        Нерозпізнані примітки не створюють записів (не вгадуємо).
        """
        from datetime import date as _date

        provisions = (
            self.db.query(LegalProvision)
            .filter(LegalProvision.document_revision_id == revision.id)
            .all()
        )
        if not provisions:
            return {"links": 0, "events": 0}

        # Індекс актів каталогу для зіставлення «№ 435-IV» → документ.
        docs_by_nreg: dict[str, LegalDocument] = {
            (d.nreg or "").lower().replace(" ", ""): d
            for d in self.db.query(LegalDocument).all()
        }

        # Дедуплікація: наявні зв'язки положень цієї редакції.
        # Ключ будується так само, як при вставці: source, target, type,
        # act_number (з source_meta_json), evidence.
        existing_links: set[tuple] = set()
        for lk in (
            self.db.query(LegalLink)
            .filter(LegalLink.source_provision_id.in_([str(p.id) for p in provisions]))
            .all()
        ):
            meta = lk.source_meta_json or {}
            existing_links.add(
                (
                    str(lk.source_provision_id),
                    str(lk.target_document_id or ""),
                    lk.link_type,
                    str(meta.get("act_number") or ""),
                    lk.evidence_text,
                )
            )
        # Наявні події, щоб повторний імпорт не дублював стрічку
        # (ключ будується з тих самих значень, що й зберігаються в рядку).
        def _event_key(affected: str, etype: str, article: str | None, act_ref: str) -> tuple:
            return (affected, etype, article, act_ref)

        existing_events: set[tuple] = {
            _event_key(str(e.affected_document_id), e.event_type, e.source_provision, e.source_act_ref)
            for e in self.db.query(LegalEvent)
            .filter(LegalEvent.affected_document_id == str(document.id))
            .all()
        }

        links_added = 0
        events_added = 0

        for prov in provisions:
            if not prov.text:
                continue
            for note in extract_change_notes(prov.text):
                target_doc = docs_by_nreg.get(note.act_number.lower().replace(" ", ""))
                resolved = target_doc is not None
                status = "resolved" if resolved else "unresolved"
                evidence = note.evidence
                # Акт-джерело в ключі: для unresolved (немає в каталозі) рядки
                # з різними актами не «склеюються» в один.
                key = (
                    str(prov.id),
                    str(target_doc.id) if target_doc else "",
                    note.link_type,
                    note.act_number,
                    evidence,
                )
                if key not in existing_links:
                    existing_links.add(key)
                    self.db.add(
                        LegalLink(
                            source_provision_id=str(prov.id),
                            target_document_id=str(target_doc.id) if target_doc else None,
                            target_provision_id=None,
                            link_type=note.link_type,
                            direction="source_to_target",
                            evidence_text=evidence,
                            resolution_status=status,
                            source_meta_json={
                                "action": note.action,
                                "act_number": note.act_number,
                                "act_date": note.act_date,
                                "article": note.article,
                                "parser": "change_notes/v1",
                            },
                        )
                    )
                    links_added += 1

                act_ref = (
                    f"№ {note.act_number} від {note.act_date}"
                    if note.act_date
                    else f"№ {note.act_number}"
                )
                event_key = _event_key(str(document.id), note.event_type, note.article, act_ref)
                if event_key not in existing_events:
                    existing_events.add(event_key)
                    event_date = None
                    if note.act_date:
                        try:
                            event_date = _date.fromisoformat(note.act_date)
                        except ValueError:  # pragma: no cover — нормалізація вже гарантує формат
                            event_date = None
                    self.db.add(
                        LegalEvent(
                            source_document_id=str(target_doc.id) if target_doc else None,
                            affected_document_id=str(document.id),
                            event_type=note.event_type,
                            source_event_date=event_date,
                            effective_date=event_date,
                            source_provision=note.article,
                            source_act_ref=act_ref,
                            source_url=revision.source_url,
                            processing_status="parsed",
                            ai_summary_status="pending",
                        )
                    )
                    events_added += 1

        self.db.commit()
        return {"links": links_added, "events": events_added}

    def _map_document_type_to_force_level(self, doc_type: str) -> str:
        """Мапує тип документа на рівень юридичної сили."""
        type_lower = (doc_type or "").lower()
        if "конституц" in type_lower:
            return "1"  # Конституція
        elif "кодекс" in type_lower:
            return "3"  # Закони та Кодекси
        elif "закон" in type_lower:
            return "3"  # Закони
        elif "постанова" in type_lower and "верховн" in type_lower:
            return "4"  # Постанови ВР
        elif "указ" in type_lower and "президент" in type_lower:
            return "5"  # Укази Президента
        elif "постанова" in type_lower and "кабінет" in type_lower:
            return "6"  # Постанови КМУ
        elif "наказ" in type_lower:
            return "7"  # Накази міністерств
        return "8"  # Інші

    def _collect_all_provisions(self, provisions: list) -> list:
        """Збирає всі положення з ієрархії в плоский список."""
        result = []
        for p in provisions:
            result.append(p)
            if p.children:
                result.extend(self._collect_all_provisions(p.children))
        return result

    def _flatten_provisions_text(self, provisions: list) -> str:
        """Об'єднує тексти всіх положень в один рядок."""
        texts = []
        for p in self._collect_all_provisions(provisions):
            if p.text:
                texts.append(p.text)
        return "\n\n".join(texts)

    def _import_provisions_recursive(self, revision: DocumentRevision, provisions: list, parent_id: str | None = None):
        """Рекурсивно імпортує положення з ієрархією."""
        for p in provisions:
            # Визначаємо article/part/point/subpoint номери
            article_num = part_num = point_num = subpoint_num = None
            if p.level == "article":
                article_num = p.number
            elif p.level == "part":
                part_num = p.number
            elif p.level == "point":
                point_num = p.number
            elif p.level == "subpoint":
                subpoint_num = p.number

            prov = self.upsert_provision(
                revision=revision,
                provision_identifier=p.identifier,
                article_number=article_num,
                part_number=part_num,
                point_number=point_num,
                subpoint_number=subpoint_num,
                heading=p.title,
                text=p.text,
                ordinal=p.ordinal,
                parent_provision_id=parent_id,
            )

            if p.children:
                self._import_provisions_recursive(revision, p.children, prov.id)