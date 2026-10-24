import uuid

from sqlalchemy import Boolean, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserMonitoringRule(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_monitoring_rules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        "user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_type: Mapped[str] = mapped_column(String(60), nullable=False)
    rule_configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    delivery_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_notified_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship(back_populates="monitoring_rules")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserMonitoringRule id={self.id} type={self.rule_type} user={self.user_id}>"