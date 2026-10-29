import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.contract_document import ContractDocument


class ContractAnalysis(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "contract_analyses"

    contract_document_id: Mapped[uuid.UUID] = mapped_column(
        "contract_document_id", String(36), ForeignKey("contract_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_version: Mapped[int] = mapped_column(nullable=False, default=1)
    source_revision_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    structured_result_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    model_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    contract_document: Mapped["ContractDocument"] = relationship(back_populates="analyses")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContractAnalysis id={self.id} contract={self.contract_document_id} v={self.analysis_version}>"