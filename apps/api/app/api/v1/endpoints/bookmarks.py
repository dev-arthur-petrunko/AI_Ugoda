"""Ендпоінти для закладок користувачів (K11 — акаунти)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_active_user
from app.core.database import get_db
from app.models.user_bookmark import UserBookmark
from app.models.legal_document import LegalDocument

router = APIRouter()


@router.get("")
async def list_bookmarks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Список закладок поточного користувача."""
    user_id = current_user["id"]
    items = (
        db.query(UserBookmark)
        .filter(UserBookmark.user_id == user_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(b.id),
                "document_id": str(b.document_id),
                "provision_identifier": b.provision_identifier,
                "note": b.note,
                "created_at": str(b.created_at),
            }
            for b in items
        ],
    }


@router.post("")
async def add_bookmark(
    document_id: str,
    provision_identifier: str | None = None,
    note: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    """Додати закладку на акт/положення."""
    user_id = current_user["id"]
    # Перевіряємо, що документ існує
    doc = db.get(LegalDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    # Уникаємо дублікатів
    existing = (
        db.query(UserBookmark)
        .filter(
            UserBookmark.user_id == user_id,
            UserBookmark.document_id == document_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Закладка вже існує")
    bookmark = UserBookmark(
        user_id=user_id,
        document_id=document_id,
        provision_identifier=provision_identifier,
        note=note,
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return {
        "id": str(bookmark.id),
        "document_id": str(bookmark.document_id),
        "provision_identifier": bookmark.provision_identifier,
        "note": bookmark.note,
        "created_at": str(bookmark.created_at),
    }


@router.delete("/{bookmark_id}")
async def remove_bookmark(
    bookmark_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, str]:
    """Видалити закладку."""
    user_id = current_user["id"]
    bookmark = (
        db.query(UserBookmark)
        .filter(UserBookmark.id == bookmark_id, UserBookmark.user_id == user_id)
        .first()
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Закладку не знайдено")
    db.delete(bookmark)
    db.commit()
    return {"status": "deleted"}
