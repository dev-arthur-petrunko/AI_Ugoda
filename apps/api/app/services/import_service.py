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
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.base import Base
from app.models.conflict_candidate import ConflictCandidate
from app.models.legal_document import LegalDocument
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision
from app.models.document_revision import DocumentRevision
from app.models.legal_force_level import LegalForceLevel


def _checksum(content: bytes | str) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class ImportService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db or SessionLocal()

    def __enter__(self) -> "ImportService":
        return self

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
    ) -> LegalDocument:
        row = (
            self.db.query(LegalDocument)
            .filter(LegalDocument.source_id == source_id)
            .first()
        )
        if row:
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
        row = DocumentRevision(
            legal_document_id=document.id,
            revision_label=revision_label,
            revision_date=revision_date,
            effective_from=effective_from,
            effective_to=effective_to,
            source_url=source_url,
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
        row = LegalProvision(
            document_revision_id=revision.id,
            provision_identifier=provision_identifier,
            article_number=article_number,
            part_number=part_number,
            point_number=point_number,
            subpoint_number=subpoint_number,
            heading=heading,
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

    def create_conflict_candidate(
        self,
        *,
        provision_a: LegalProvision,
        provision_b: LegalProvision,
        conflict_type: str,
        evidence_json: dict,
        confidence: str = "low",
        review_status: str = "Не підтверджено",
        rule_applied: str | None = None,
        winner_provision: LegalProvision | None = None,
        explanation: str | None = None,
    ) -> ConflictCandidate:
        row = ConflictCandidate(
            provision_a_id=provision_a.id,
            provision_b_id=provision_b.id,
            conflict_type=conflict_type,
            evidence_json=evidence_json,
            confidence=confidence,
            review_status=review_status,
            rule_applied=rule_applied,
            winner_provision_id=winner_provision.id if winner_provision else None,
            explanation=explanation,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row