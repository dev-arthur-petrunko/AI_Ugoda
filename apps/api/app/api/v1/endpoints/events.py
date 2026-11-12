"""§4.3: стрічка «Нові зміни» з legal_events (офіційні примітки джерела).

Не сортування списку актів, а реальні події: яку саме статтю і яким актом
змінено/виключено/доповнено, з датою та посиланням на джерело.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.legal_document import LegalDocument
from app.models.legal_event import LegalEvent

router = APIRouter()

# Підписи дій для UI (українською); значення — event_type з примітки джерела.
EVENT_LABELS: dict[str, str] = {
    "amends": "Змінено",
    "adds": "Доповнено",
    "excludes": "Виключено",
    "replaces": "Нова редакція",
    "repeals": "Втратило чинність",
}


@router.get("")
async def list_events(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    document_id: str | None = Query(None, description="Фільтр за актом"),
    event_type: str | None = Query(None, description="Фільтр за дією"),
    db: Session = Depends(get_db),
):
    """Стрічка подій змін: спершу найновіші за датою зміни в джерелі."""
    q = db.query(LegalEvent)
    if document_id:
        q = q.filter(LegalEvent.affected_document_id == document_id)
    if event_type:
        q = q.filter(LegalEvent.event_type == event_type)

    total = q.count()
    rows = (
        q.order_by(
            # Дата події першочергова; нульові (не розібрані) — в кінець.
            LegalEvent.source_event_date.is_(None),
            desc(LegalEvent.source_event_date),
            desc(LegalEvent.created_at),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Назви актів для клікабельності (affected + source, якщо є в каталозі).
    needed = {str(e.affected_document_id) for e in rows}
    needed |= {str(e.source_document_id) for e in rows if e.source_document_id}
    titles: dict[str, str] = {}
    if needed:
        for d in db.query(LegalDocument).filter(LegalDocument.id.in_(list(needed))).all():
            titles[str(d.id)] = d.title

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "event_label": EVENT_LABELS.get(e.event_type, e.event_type),
                "source_provision": e.source_provision,
                "source_act_ref": e.source_act_ref,
                "source_event_date": (
                    e.source_event_date.isoformat() if e.source_event_date else None
                ),
                "affected_document_id": str(e.affected_document_id),
                "affected_title": titles.get(str(e.affected_document_id), ""),
                "source_document_id": str(e.source_document_id) if e.source_document_id else None,
                "source_title": (
                    titles.get(str(e.source_document_id)) if e.source_document_id else None
                ),
                "source_url": e.source_url,
                "found_by": "code",  # L1: знайдено програмою (не ШІ)
            }
            for e in rows
        ],
    }


@router.get("/{event_id}")
async def get_event(event_id: str, db: Session = Depends(get_db)):
    """Деталі події з доказом (примітка з тексту джерела)."""
    e = db.get(LegalEvent, event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Подію не знайдено")
    return {
        "id": str(e.id),
        "event_type": e.event_type,
        "event_label": EVENT_LABELS.get(e.event_type, e.event_type),
        "source_provision": e.source_provision,
        "source_act_ref": e.source_act_ref,
        "source_event_date": (
            e.source_event_date.isoformat() if e.source_event_date else None
        ),
        "affected_document_id": str(e.affected_document_id),
        "source_document_id": str(e.source_document_id) if e.source_document_id else None,
        "source_url": e.source_url,
        "processing_status": e.processing_status,
        "found_by": "code",
    }
