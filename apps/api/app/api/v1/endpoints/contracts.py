"""Ендпоінти для договорів користувачів (K11 — акаунти,アナліз договорів)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.contract_document import ContractDocument

router = APIRouter()


@router.get("")
async def list_contracts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Список договорів поточного користувача."""
    user_id = current_user["id"]
    items = (
        db.query(ContractDocument)
        .filter(ContractDocument.owner_id == user_id)
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
                "id": str(c.id),
                "original_filename": c.original_filename,
                "content_type": c.content_type,
                "size_bytes": c.size_bytes,
                "processing_status": c.processing_status,
                "retention_policy": c.retention_policy,
                "created_at": str(c.created_at),
            }
            for c in items
        ],
    }


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    """Отримати деталі договору."""
    user_id = current_user["id"]
    contract = (
        db.query(ContractDocument)
        .filter(ContractDocument.id == contract_id, ContractDocument.owner_id == user_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Договір не знайдено")
    return {
        "id": str(contract.id),
        "original_filename": contract.original_filename,
        "content_type": contract.content_type,
        "size_bytes": contract.size_bytes,
        "file_metadata": contract.file_metadata,
        "processing_status": contract.processing_status,
        "retention_policy": contract.retention_policy,
        "created_at": str(contract.created_at),
    }


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, str]:
    """Видалити договір (м'яке видалення)."""
    user_id = current_user["id"]
    contract = (
        db.query(ContractDocument)
        .filter(ContractDocument.id == contract_id, ContractDocument.owner_id == user_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Договір не знайдено")
    contract.deleted_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    db.commit()
    return {"status": "deleted"}
