from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_provision import LegalProvision

router = APIRouter()


@router.get("/{document_id}/analysis")
async def get_analysis(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Базова аналітика акта (без ІІ) — метрики з коду."""
    doc = db.get(LegalDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Акт не знайдено")

    revisions = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).all()
    provisions = []
    for rev in revisions:
        provs = db.query(LegalProvision).filter(LegalProvision.document_revision_id == rev.id).all()
        provisions.extend(provs)

    # Basic metrics
    return {
        "document_id": document_id,
        "title": doc.title,
        "status": doc.current_known_status,
        "legal_force_level": doc.legal_force_level,
        "metrics": {
            "revisions_count": len(revisions),
            "provisions_count": len(provisions),
            "articles_count": len([p for p in provisions if p.article_number]),
            "parts_count": len([p for p in provisions if p.part_number]),
            "points_count": len([p for p in provisions if p.point_number]),
        },
        "revisions": [
            {
                "id": str(r.id),
                "label": r.revision_label,
                "effective_from": r.effective_from.isoformat() if r.effective_from else None,
                "effective_to": r.effective_to.isoformat() if r.effective_to else None,
                "verification_status": r.verification_status,
            }
            for r in revisions
        ],
    }
