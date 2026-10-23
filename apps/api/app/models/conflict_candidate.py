import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    conflict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[str] = mapped_column(String(40), nullable=False, default="low")
    review_status: Mapped[str] = mapped_column(String(60), nullable=False, default="Не підтверджено")

    provision_a: Mapped["LegalProvision"] = relationship(foreign_keys=[provision_a_id])
    provision_b: Mapped["LegalProvision"] = relationship(foreign_keys=[provision_b_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ConflictCandidate id={self.id} type={self.conflict_type} status={self.review_status}>"