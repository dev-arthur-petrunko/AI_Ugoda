from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.contract_document import ContractDocument


class User(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default="uk", nullable=False)

    bookmarks: Mapped[list["UserBookmark"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    monitoring_rules: Mapped[list["UserMonitoringRule"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    contract_documents: Mapped[list["ContractDocument"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys=[ContractDocument.owner_id],
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email}>"