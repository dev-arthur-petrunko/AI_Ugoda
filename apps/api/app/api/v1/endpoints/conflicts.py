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
    items = [
        {
            "id": str(c.id) if c.id is not None else f"{c.conflict_type}:{c.provision_a_id}:{c.provision_b_id}",
            "conflict_type": c.conflict_type,
            "confidence": c.confidence,
            "review_status": c.review_status,
            "rule_applied": c.rule_applied,
            "explanation": c.explanation,
            "provision_a_id": str(c.provision_a_id),
            "provision_b_id": str(c.provision_b_id),
            "winner_provision_id": str(c.winner_provision_id) if c.winner_provision_id else None,
        }
        for c in conflicts
    ]
    return {"items": items, "total": len(items)}


@router.get("/{conflict_id}")
async def get_conflict(conflict_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Деталі колізії."""
    return {"id": conflict_id, "detail": "Not implemented yet"}


@router.patch("/{conflict_id}")
async def update_conflict(conflict_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Підтвердити/відхилити колізію (expert)."""
    return {"id": conflict_id, "status": "updated"}