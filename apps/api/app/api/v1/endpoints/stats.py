from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision

router = APIRouter()


@router.get("")
async def stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {
        "documents": db.query(LegalDocument).count(),
        "revisions": db.query(DocumentRevision).count(),
        "provisions": db.query(LegalProvision).count(),
        "links": db.query(LegalLink).count(),
    }
