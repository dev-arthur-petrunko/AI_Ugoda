import uuid
from datetime import date

from sqlalchemy import Date, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class DocumentRevision(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "document_revisions"

    legal_document_id: Mapped[uuid.UUID] = mapped_column(
        "legal_document_id",
        UUID(as_uuid=True),
        ForeignKey("legal_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    revision_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    imported_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    original_content_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    imported_at: Mapped[Date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unverified")

    document: Mapped["LegalDocument"] = relationship(back_populates="revisions")
    provisions: Mapped[list["LegalProvision"]] = relationship(
        back_populates="revision", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentRevision id={self.id} label={self.revision_label} doc={self.legal_document_id}>"