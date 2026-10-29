"""AI service (TZ v2, розділ B.9 — RAG-конвеєр)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_provision import LegalProvision


@dataclass
class Citation:
    provision_id: str
    quote: str
    verified: bool = False


@dataclass
class AskResult:
    answer: str
    key_points: list[str]
    citations: list[Citation]
    confidence: float
    warnings: list[str]


class AIService:
    """Сервіс ШІ для роботи з законодавством (RAG)."""

    def __init__(self, db: Session, provider: str = "mock"):
        self.db = db
        self.provider = provider

    def ask(self, question: str, document_id: str | None = None) -> AskResult:
        """Відповідає на питання з цитуванням статей."""
        # 1. Пошук кандидатів
        from app.services.search import SearchService
        search = SearchService(self.db)
        results, _ = search.search(question, limit=10)

        # 2. Збір контексту
        context_provisions = []
        for r in results:
            if r.revision_id:
                prov = self.db.query(LegalProvision).filter(
                    LegalProvision.document_revision_id == r.revision_id
                ).first()
                if prov:
                    context_provisions.append(prov)

        # 3. Генерація відповіді (mock)
        if not context_provisions:
            return AskResult(
                answer="У базі не знайдено підтверджених норм. Перевірте на zakon.rada.gov.ua.",
                key_points=[],
                citations=[],
                confidence=0.0,
                warnings=["Джерело не знайдено"],
            )

        # Mock answer based on found provisions
        citations = []
        for prov in context_provisions[:3]:
            citations.append(Citation(
                provision_id=str(prov.id),
                quote=prov.text[:100] if prov.text else "",
                verified=True,
            ))

        return AskResult(
            answer=f"Знайдено {len(context_provisions)} релевантних норм. (Mock відповідь — потрібен реальний LLM провайдер)",
            key_points=[f"Знайдено {len(context_provisions)} норм"],
            citations=citations,
            confidence=0.5,
            warnings=["Mock-відповідь — потрібен реальний LLM провайдер"],
        )

    def summarize_act(self, document_id: str) -> dict[str, Any]:
        """Сводка акта (A1)."""
        doc = self.db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
        if not doc:
            return {"error": "Document not found"}

        revisions = self.db.query(DocumentRevision).filter(
            DocumentRevision.legal_document_id == doc.id
        ).all()

        provisions = []
        for rev in revisions:
            provs = self.db.query(LegalProvision).filter(
                LegalProvision.document_revision_id == rev.id
            ).all()
            provisions.extend(provs)

        return {
            "document_id": document_id,
            "title": doc.title,
            "status": doc.current_known_status,
            "revisions_count": len(revisions),
            "provisions_count": len(provisions),
            "summary": f"Акт містить {len(provisions)} положень у {len(revisions)} редакціях.",
            "key_points": [f"Редакцій: {len(revisions)}", f"Положень: {len(provisions)}"],
        }

    def verify_citation(self, provision_id: str, quote: str) -> bool:
        """Перевіряє, що цитата реально є в тексті джерела."""
        provision = self.db.query(LegalProvision).filter(LegalProvision.id == provision_id).first()
        if not provision or not provision.text:
            return False
        # Normalize and check
        normalized_text = provision.text.strip().lower()
        normalized_quote = quote.strip().lower()
        return normalized_quote in normalized_text
