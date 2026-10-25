from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class LegalForceLevel(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "legal_force_levels"

    level: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)  # 1..8 (1 — найвища)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Наприклад «Конституція України»
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # для колізій


    def __repr__(self) -> str:  # pragma: no cover
        return f"<LegalForceLevel level={self.level} name={self.name}>"