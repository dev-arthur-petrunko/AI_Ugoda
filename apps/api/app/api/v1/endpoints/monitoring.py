"""Ендпоінти для правил моніторингу користувачів (K11 — акаунти)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.monitoring_rule import UserMonitoringRule

router = APIRouter()


@router.get("")
async def list_monitoring_rules(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Список правил моніторингу поточного користувача."""
    user_id = current_user["id"]
    items = (
        db.query(UserMonitoringRule)
        .filter(UserMonitoringRule.user_id == user_id)
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
                "id": str(r.id),
                "rule_type": r.rule_type,
                "rule_configuration": r.rule_configuration,
                "delivery_preferences": r.delivery_preferences,
                "enabled": r.enabled,
                "last_notified_at": r.last_notified_at,
                "created_at": str(r.created_at),
            }
            for r in items
        ],
    }


@router.post("")
async def create_monitoring_rule(
    rule_type: str,
    rule_configuration: dict[str, Any] | None = None,
    delivery_preferences: dict[str, Any] | None = None,
    enabled: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, Any]:
    """Створити правило моніторингу."""
    user_id = current_user["id"]
    rule = UserMonitoringRule(
        user_id=user_id,
        rule_type=rule_type,
        rule_configuration=rule_configuration or {},
        delivery_preferences=delivery_preferences or {},
        enabled=enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {
        "id": str(rule.id),
        "rule_type": rule.rule_type,
        "rule_configuration": rule.rule_configuration,
        "delivery_preferences": rule.delivery_preferences,
        "enabled": rule.enabled,
        "created_at": str(rule.created_at),
    }


@router.delete("/{rule_id}")
async def delete_monitoring_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> dict[str, str]:
    """Видалити правило моніторингу."""
    user_id = current_user["id"]
    rule = (
        db.query(UserMonitoringRule)
        .filter(UserMonitoringRule.id == rule_id, UserMonitoringRule.user_id == user_id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не знайдено")
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}
