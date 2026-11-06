from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision

router = APIRouter()


@router.get("")
async def stats(db: Session = Depends(get_db)):
    by_origin = dict(
        db.query(LegalDocument.data_origin, func.count(LegalDocument.id))
        .group_by(LegalDocument.data_origin)
        .all()
    )
    total = db.query(LegalDocument).count()
    return {
        "documents": total,
        "revisions": db.query(DocumentRevision).count(),
        "provisions": db.query(LegalProvision).count(),
        "links": db.query(LegalLink).count(),
        # S3.2: окремі лічильники по походженню даних
        "documents_official": by_origin.get("official", 0),
        "documents_fixture": by_origin.get("fixture", 0),
        "has_official": by_origin.get("official", 0) > 0,
    }
