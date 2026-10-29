import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.legal_provision import LegalProvision


class LegalReference(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "legal_references"

    source_provision_id: Mapped[uuid.UUID] = mapped_column(
        "source_provision_id", String(36), ForeignKey("legal_provisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_document_id: Mapped[uuid.UUID | None] = mapped_column(
        "target_document_id", String(36), ForeignKey("legal_documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_provision_identifier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reference_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unresolved")
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_provision: Mapped["LegalProvision"] = relationship(foreign_keys=[source_provision_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalReference id={self.id} type={self.reference_type}>"