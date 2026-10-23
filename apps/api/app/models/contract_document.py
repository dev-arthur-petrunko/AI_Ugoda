import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ContractDocument(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "contract_documents"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        "owner_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        "workspace_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    secure_storage_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    file_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    processing_status: Mapped[str] = mapped_column(String(40), nullable=False, default="uploaded")
    retention_policy: Mapped[str] = mapped_column(String(60), nullable=False, default="configurable")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="contract_documents", foreign_keys=[owner_id])
    analyses: Mapped[list["ContractAnalysis"]] = relationship(back_populates="contract_document", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContractDocument id={self.id} name={self.original_filename} status={self.processing_status}>"