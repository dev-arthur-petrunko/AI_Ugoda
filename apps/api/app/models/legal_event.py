import uuid
from datetime import date

from sqlalchemy import Date, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class LegalEvent(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "legal_events"

    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        "source_document_id", UUID(as_uuid=True), ForeignKey("legal_documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    affected_document_id: Mapped[uuid.UUID] = mapped_column(
        "affected_document_id", UUID(as_uuid=True), ForeignKey("legal_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    discovered_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    old_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        "old_revision_id", UUID(as_uuid=True), ForeignKey("document_revisions.id", ondelete="SET NULL"), nullable=True
    )
    new_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        "new_revision_id", UUID(as_uuid=True), ForeignKey("document_revisions.id", ondelete="SET NULL"), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    ai_summary_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")

    affected_document: Mapped["LegalDocument"] = relationship(back_populates="events", foreign_keys=[affected_document_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalEvent id={self.id} type={self.event_type} affected={self.affected_document_id}>"