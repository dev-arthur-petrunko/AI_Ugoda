from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AIAnalysis(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "ai_analyses"

    analysis_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column("target_id", String(36), nullable=False, index=True)
    model_provider: Mapped[str] = mapped_column(String(60), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_revision_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    structured_result_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    analysis_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIAnalysis id={self.id} type={self.analysis_type} status={self.analysis_status}>"