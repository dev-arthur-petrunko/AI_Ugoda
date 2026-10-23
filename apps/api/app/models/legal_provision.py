import uuid

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class LegalProvision(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "legal_provisions"

    document_revision_id: Mapped[uuid.UUID] = mapped_column(
        "document_revision_id",
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provision_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    parent_provision_id: Mapped[uuid.UUID | None] = mapped_column(
        "parent_provision_id",
        UUID(as_uuid=True),
        ForeignKey("legal_provisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    revision: Mapped["DocumentRevision"] = relationship(back_populates="provisions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalProvision id={self.id} ident={self.provision_identifier}>"