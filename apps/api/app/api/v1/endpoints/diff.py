from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument

router = APIRouter()


@router.get("/{document_id}/diff")
async def get_diff(document_id: str, from_rev: str, to_rev: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Порівняння двох редакцій акта (diff)."""
    doc = db.get(LegalDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Акт не знайдено")

    rev_from = db.get(DocumentRevision, from_rev)
    rev_to = db.get(DocumentRevision, to_rev)

    if not rev_from or not rev_to:
        raise HTTPException(status_code=404, detail="Редакцію не знайдено")

    # Simple text diff
    text_from = rev_from.normalized_text or ""
    text_to = rev_to.normalized_text or ""

    # Split into lines for diff
    lines_from = text_from.split("\n")
    lines_to = text_to.split("\n")

    # Simple diff: find added/removed/changed lines
    added = []
    removed = []

    for line in lines_to:
        if line.strip() and line not in lines_from:
            added.append(line.strip())

    for line in lines_from:
        if line.strip() and line not in lines_to:
            removed.append(line.strip())

    return {
        "document_id": document_id,
        "from_revision": from_rev,
        "to_revision": to_rev,
        "from_date": rev_from.effective_from.isoformat() if rev_from.effective_from else None,
        "to_date": rev_to.effective_from.isoformat() if rev_to.effective_from else None,
        "added": added[:50],
        "removed": removed[:50],
        "changed_count": len(added) + len(removed),
    }
