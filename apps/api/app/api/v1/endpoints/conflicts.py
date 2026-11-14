"""§6: колізії — збережені кандидати, деталі, рішення експерта."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.conflict_candidate import ConflictCandidate
from app.services.conflict_engine import ConflictEngine

router = APIRouter()


class ReviewUpdate(BaseModel):
    """Рішення експерта: підтверджено / відхилено."""

    review_status: str = Field(pattern="^(Підтверджено|Відхилено)$")


def _serialize(c: ConflictCandidate) -> dict:
    return {
        "id": str(c.id),
        "conflict_type": c.conflict_type,
        "confidence": c.confidence,
        "review_status": c.review_status,
        "rule_applied": c.rule_applied,
        "explanation": c.explanation,
        "evidence": c.evidence_json or {},
        "found_by": c.source_of_detection,  # code | ai | expert
        "reviewed_by": c.reviewed_by,
        "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
        "provision_a_id": str(c.provision_a_id),
        "provision_b_id": str(c.provision_b_id),
        "winner_provision_id": str(c.winner_provision_id) if c.winner_provision_id else None,
    }


@router.get("/")
async def list_conflicts(
    limit: int = 50,
    offset: int = 0,
    review_status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Список збережених кандидатів (усі — «Не підтверджено» до експерта).

    Читання без сканування: повний `run_all` у async-ендпоінті блокував
    event loop (таймаути інших запитів). Оновлення — POST /conflicts/scan.
    """
    q = db.query(ConflictCandidate)
    if review_status:
        q = q.filter(ConflictCandidate.review_status == review_status)
    total = q.count()
    rows = (
        q.order_by(ConflictCandidate.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"items": [_serialize(c) for c in rows], "total": total}


@router.post("/scan")
async def scan_conflicts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Запустити детектори й зберегти нових кандидатів (ідемпотентно)."""
    candidates = ConflictEngine(db).run_all(persist=True)
    return {"total": len(candidates), "items": [_serialize(c) for c in candidates]}


@router.get("/{conflict_id}")
async def get_conflict(
    conflict_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Деталі кандидата: дві норми, доказ (цитати), правило, статус експерта."""
    c = db.get(ConflictCandidate, conflict_id)
    if not c:
        raise HTTPException(status_code=404, detail="Кандидата не знайдено")
    data = _serialize(c)
    data["provision_a"] = {
        "id": str(c.provision_a.id),
        "identifier": c.provision_a.provision_identifier,
        "article_number": c.provision_a.article_number,
        "text": (c.provision_a.text or "")[:600],
    }
    data["provision_b"] = {
        "id": str(c.provision_b.id),
        "identifier": c.provision_b.provision_identifier,
        "article_number": c.provision_b.article_number,
        "text": (c.provision_b.text or "")[:600],
    }
    return data


@router.patch("/{conflict_id}")
async def update_conflict(
    conflict_id: str,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Підтвердити/відхилити кандидата (рішення експерта з іменем і датою)."""
    if not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=403, detail="Потрібні права експерта (адмін)"
        )
    c = db.get(ConflictCandidate, conflict_id)
    if not c:
        raise HTTPException(status_code=404, detail="Кандидата не знайдено")
    c.review_status = payload.review_status
    c.reviewed_by = current_user.get("email") or current_user.get("sub") or "admin"
    c.reviewed_at = datetime.now(UTC)
    c.source_of_detection = "expert" if payload.review_status == "Підтверджено" else c.source_of_detection
    db.commit()
    db.refresh(c)
    return _serialize(c)
