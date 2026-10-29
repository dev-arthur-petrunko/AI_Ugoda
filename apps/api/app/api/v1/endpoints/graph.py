from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get("/{document_id}")
async def get_graph(document_id: str, depth: int = 2, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Дані для графа зв'язків акта."""
    return {"document_id": document_id, "depth": depth, "nodes": [], "edges": []}