from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.conflict_engine import ConflictEngine

router = APIRouter()


@router.get("/")
async def list_conflicts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Список колізій (кандидатів)."""
    engine = ConflictEngine(db)
    conflicts = engine.run_all()
    return {"items": conflicts, "total": len(conflicts)}


@router.get("/{conflict_id}")
async def get_conflict(conflict_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Деталі колізії."""
    return {"id": conflict_id, "detail": "Not implemented yet"}


@router.patch("/{conflict_id}")
async def update_conflict(conflict_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Підтвердити/відхилити колізію (expert)."""
    return {"id": conflict_id, "status": "updated"}