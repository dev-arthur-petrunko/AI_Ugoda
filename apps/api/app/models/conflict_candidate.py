import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConflictCandidate(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "conflict_candidates"

    provision_a_id: Mapped[uuid.UUID] = mapped_column(
        "provision_a_id", UUID(as_uuid=True), ForeignKey("legal_provisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provision_b_id: Mapped[uuid.UUID] = mapped_column(
        "provision_b_id", UUID(as_uuid=True), ForeignKey("legal_provisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conflict_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)  # HIERARCHY_CONFLICT, SPECIAL_VS_GENERAL, SAME_LEVEL_NEWER, DEAD_REFERENCE, GHOST_NORM, CODE_DUPLICATION, UNCONSTITUTIONAL, EXPIRING, EU_MISMATCH
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[str] = mapped_column(String(40), nullable=False, default="low")  # low | medium | high
    review_status: Mapped[str] = mapped_column(String(60), nullable=False, default="Не підтверджено")  # candidate | confirmed | dismissed
    rule_applied: Mapped[str | None] = mapped_column(String(100), nullable=True)  # яке правило колізій застосовано
    winner_provision_id: Mapped[uuid.UUID | None] = mapped_column(
        "winner_provision_id", UUID(as_uuid=True), ForeignKey("legal_provisions.id", ondelete="SET NULL"), nullable=True
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)  # чitse объяснення з посиланням на правило

    provision_a: Mapped["LegalProvision"] = relationship(foreign_keys=[provision_a_id])
    provision_b: Mapped["LegalProvision"] = relationship(foreign_keys=[provision_b_id])
    winner_provision: Mapped["LegalProvision"] = relationship(foreign_keys=[winner_provision_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ConflictCandidate id={self.id} type={self.conflict_type} status={self.review_status}>"