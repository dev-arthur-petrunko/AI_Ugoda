from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/ask")
async def ask_question(question: str, document_id: str | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Відповідає на питання з цитуванням статей (RAG)."""
    ai = AIService(db)
    result = ai.ask(question, document_id)
    return {
        "answer": result.answer,
        "key_points": result.key_points,
        "citations": [{"provision_id": c.provision_id, "quote": c.quote, "verified": c.verified} for c in result.citations],
        "confidence": result.confidence,
        "warnings": result.warnings,
        "provider": result.provider,
    }


@router.get("/documents/{document_id}/summary")
async def get_summary(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Сводка акта (A1)."""
    ai = AIService(db)
    return ai.summarize_act(document_id)