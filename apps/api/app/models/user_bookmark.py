import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserBookmark(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        "user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        "document_id", String(36), ForeignKey("legal_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provision_identifier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user: Mapped["User"] = relationship(back_populates="bookmarks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserBookmark id={self.id} user={self.user_id} doc={self.document_id}>"