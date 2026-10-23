from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter()


@router.get("")
async def list_documents(
    q: Optional[str] = Query(None, description="Пошуковий запит (назва/текст/номер)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.legal_document import LegalDocument

    query = db.query(LegalDocument)
    if q:
        like = f"%{q}%"
        query = query.filter(LegalDocument.title.ilike(like))
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(d.id),
                "source_id": d.source_id,
                "title": d.title,
                "document_type": d.document_type,
                "document_number": d.document_number,
                "adoption_date": d.adoption_date.isoformat() if d.adoption_date else None,
                "issuing_authority": d.issuing_authority,
                "current_known_status": d.current_known_status,
                "source_url": d.source_url,
            }
            for d in items
        ],
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.legal_document import LegalDocument
    from app.models.document_revision import DocumentRevision
    from uuid import UUID

    doc = db.get(LegalDocument, UUID(document_id))
    if not doc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Документ не знайдено")
    revisions = (
        db.query(DocumentRevision)
        .filter(DocumentRevision.legal_document_id == doc.id)
        .order_by(DocumentRevision.revision_date.desc().nullslast())
        .all()
    )
    return {
        "id": str(doc.id),
        "source_id": doc.source_id,
        "title": doc.title,
        "document_type": doc.document_type,
        "document_number": doc.document_number,
        "adoption_date": doc.adoption_date.isoformat() if doc.adoption_date else None,
        "issuing_authority": doc.issuing_authority,
        "current_known_status": doc.current_known_status,
        "source_url": doc.source_url,
        "source_metadata_json": doc.source_metadata_json,
        "revisions": [
            {
                "id": str(r.id),
                "revision_label": r.revision_label,
                "revision_date": r.revision_date.isoformat() if r.revision_date else None,
                "valid_from": r.valid_from.isoformat() if r.valid_from else None,
                "valid_to": r.valid_to.isoformat() if r.valid_to else None,
                "source_url": r.source_url,
                "source_checksum": r.source_checksum,
                "verification_status": r.verification_status,
            }
            for r in revisions
        ],
    }