import uuid

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from app.models.base import Base, TimestampMixin, UUIDMixin


class LegalProvision(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "legal_provisions"

    document_revision_id: Mapped[uuid.UUID] = mapped_column(
        "document_revision_id",
        String(36),
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provision_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    article_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    part_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    point_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subpoint_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parent_provision_id: Mapped[uuid.UUID | None] = mapped_column(
        "parent_provision_id",
        String(36),
        ForeignKey("legal_provisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    revision: Mapped["DocumentRevision"] = relationship(back_populates="provisions")

    @declared_attr.directive
    def parent(cls) -> Mapped["LegalProvision"]:
        return relationship(
            "LegalProvision",
            remote_side=[cls.id],
            back_populates="children",
        )

    children: Mapped[list["LegalProvision"]] = relationship(back_populates="parent")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalProvision id={self.id} ident={self.provision_identifier}>"