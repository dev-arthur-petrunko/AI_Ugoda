from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.legal_event import LegalEvent


class LegalDocument(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "legal_documents"

    source_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    official_identifier: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    nreg: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)  # реєстраційний номер в ВР
    adoption_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    legal_force_level: Mapped[str | None] = mapped_column(String(40), nullable=True)  # рівень юридичної сили
    current_known_status: Mapped[str] = mapped_column(String(60), nullable=False, default="Статус потребує перевірки")
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # норма на час воєнного стану тощо
    valid_until_condition: Mapped[str | None] = mapped_column(String(500), nullable=True)  # умовна дата дії (наприклад «для дії воєнного стану»)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    revisions: Mapped[list["DocumentRevision"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentRevision.revision_date.desc()"
    )
    events: Mapped[list["LegalEvent"]] = relationship(
        back_populates="affected_document",
        cascade="all, delete-orphan",
        foreign_keys=[LegalEvent.affected_document_id],
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalDocument id={self.id} source_id={self.source_id} title={self.title[:40]}>"