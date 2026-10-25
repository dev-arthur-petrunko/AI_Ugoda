from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AuditLog(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[str | None] = mapped_column("actor_id", String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_id: Mapped[str | None] = mapped_column("target_id", String(36), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id} action={self.action} actor={self.actor_id}>"