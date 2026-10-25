from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.search import SearchService, SearchFilters

router = APIRouter()


@router.get("")
async def list_documents(
    q: Optional[str] = Query(None, description="Пошуковий запит (назва/текст/номер)"),
    document_type: Optional[str] = Query(None, description="Тип документа"),
    status: Optional[str] = Query(None, description="Статус документа"),
    issuing_authority: Optional[str] = Query(None, description="Орган, що видав"),
    adoption_date_from: Optional[str] = Query(None, description="Дата прийняття від (YYYY-MM-DD)"),
    adoption_date_to: Optional[str] = Query(None, description="Дата прийняття до (YYYY-MM-DD)"),
    legal_force_level: Optional[str] = Query(None, description="Рівень юридичної сили"),
    only_current: bool = Query(True, description="Тільки актуальні редакції"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    search_service = SearchService(db)
    filters = SearchFilters(
        document_type=document_type,
        status=status,
        issuing_authority=issuing_authority,
        adoption_date_from=adoption_date_from,
        adoption_date_to=adoption_date_to,
        legal_force_level=legal_force_level,
        only_current=only_current,
    )
    items, total = search_service.search(q or "", filters, limit, offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": item.id,
                "source_id": item.source_id,
                "title": item.title,
                "document_type": item.document_type,
                "document_number": item.document_number,
                "adoption_date": item.adoption_date,
                "issuing_authority": item.issuing_authority,
                "current_known_status": item.current_known_status,
                "source_url": item.source_url,
                "revision_id": item.revision_id,
                "revision_date": item.revision_date,
            }
            for item in items
        ],
    }


@router.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=2, description="Часткова назва для автозаповнення"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    search_service = SearchService(db)
    suggestions = search_service.get_suggestions(q, limit)
    return {"suggestions": suggestions}


@router.get("/search/by-provision")
async def search_by_provision(
    provision_ref: str = Query(..., description="Посилання на статтю (напр. 'Стаття 15')"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    search_service = SearchService(db)
    items = search_service.search_by_provision(provision_ref)
    return {
        "items": [
            {
                "id": item.id,
                "source_id": item.source_id,
                "title": item.title,
                "document_type": item.document_type,
                "document_number": item.document_number,
                "adoption_date": item.adoption_date,
                "issuing_authority": item.issuing_authority,
                "current_known_status": item.current_known_status,
                "source_url": item.source_url,
                "revision_id": item.revision_id,
                "revision_date": item.revision_date,
                "matched_provision": item.matched_provision,
            }
            for item in items
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
    doc = db.get(LegalDocument, document_id)
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
                "effective_from": r.effective_from.isoformat() if r.effective_from else None,
                "effective_to": r.effective_to.isoformat() if r.effective_to else None,
                "source_url": r.source_url,
                "source_checksum": r.source_checksum,
                "verification_status": r.verification_status,
            }
            for r in revisions
        ],
    }


@router.get("/{document_id}/provisions")
async def get_provisions(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.legal_document import LegalDocument
    from app.models.document_revision import DocumentRevision
    from app.models.legal_provision import LegalProvision
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    rev = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).order_by(DocumentRevision.revision_date.desc().nullslast()).first()
    if not rev:
        return {"document_id": document_id, "revision_id": None, "items": []}
    provs = db.query(LegalProvision).filter(LegalProvision.document_revision_id == rev.id).order_by(LegalProvision.ordinal.asc().nullslast()).all()
    def node(p):
        return {"id": str(p.id), "parent_id": str(p.parent_provision_id) if p.parent_provision_id else None, "identifier": p.provision_identifier, "article_number": p.article_number, "heading": p.heading, "text": p.text, "ordinal": p.ordinal}
    return {"document_id": document_id, "revision_id": str(rev.id), "items": [node(p) for p in provs]}


@router.get("/{document_id}/revisions")
async def get_revisions(document_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.legal_document import LegalDocument
    from app.models.document_revision import DocumentRevision
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    revisions = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).order_by(DocumentRevision.revision_date.desc().nullslast()).all()
    return {"document_id": document_id, "items": [{"id": str(r.id), "label": r.revision_label, "revision_date": r.revision_date.isoformat() if r.revision_date else None, "effective_from": r.effective_from.isoformat() if r.effective_from else None, "effective_to": r.effective_to.isoformat() if r.effective_to else None, "source_url": r.source_url, "verification_status": r.verification_status} for r in revisions]}


@router.get("/{document_id}/at")
async def get_at(document_id: str, date: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from datetime import date as ddate
    from app.models.legal_document import LegalDocument
    from app.models.document_revision import DocumentRevision
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    try:
        target = ddate.fromisoformat(date)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Невірний формат дати (YYYY-MM-DD)")
    revs = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).all()
    chosen = None
    for r in revs:
        if r.effective_from and r.effective_from <= target and (r.effective_to is None or r.effective_to >= target):
            chosen = r
            break
    if chosen is None:
        if revs:
            chosen = sorted(revs, key=lambda r: r.effective_from or ddate.min)[-1]
    if chosen is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Редакцію не знайдено")
    return {"document_id": document_id, "date": date, "revision_id": str(chosen.id), "effective_from": chosen.effective_from.isoformat() if chosen.effective_from else None, "effective_to": chosen.effective_to.isoformat() if chosen.effective_to else None}
