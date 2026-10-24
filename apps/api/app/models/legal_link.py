import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class LegalLink(Base, TimestampMixin, UUIDMixin):
    """
    Зв'язок між положеннями/актами: змінює, скасовує, посилається, виконує, трактує, гармонізує.
    Джерело зв'язку — метадані порталу або регулярний вираз з тексту.
    """
    __tablename__ = "legal_links"

    source_provision_id: Mapped[uuid.UUID] = mapped_column(
        "source_provision_id", String(36), ForeignKey("legal_provisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_provision_id: Mapped[uuid.UUID | None] = mapped_column(
        "target_provision_id", String(36), ForeignKey("legal_provisions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_document_id: Mapped[uuid.UUID | None] = mapped_column(
        "target_document_id", String(36), ForeignKey("legal_documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    link_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)  # amends | repeals | refers_to | implements | interprets | harmonizes_with
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="source_to_target")  # source->target або target->source
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # фрагмент тексту, де знайдено посилання
    resolution_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unresolved")  # resolved | unresolved | candidate
    source_meta_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    source_provision: Mapped["LegalProvision"] = relationship(foreign_keys=[source_provision_id])
    target_provision: Mapped["LegalProvision"] = relationship(foreign_keys=[target_provision_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalLink id={self.id} type={self.link_type}>"