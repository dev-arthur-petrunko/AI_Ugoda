"""Risk assessment module (TZ v2, розділ B.7)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.document_revision import DocumentRevision
from app.models.legal_provision import LegalProvision


@dataclass
class RiskFactors:
    sanction_severity: float = 0.0
    fine_size: float = 0.0
    deadline_proximity: float = 0.0
    recent_change: float = 0.0
    ambiguity: float = 0.0
    confirmed_conflict: float = 0.0
    temporary_norm: float = 0.0
    ghost_norm: float = 0.0

    def total_score(self) -> int:
        score = (
            30 * self.sanction_severity
            + 15 * self.fine_size
            + 15 * self.deadline_proximity
            + 10 * self.recent_change
            + 10 * self.ambiguity
            + 10 * self.confirmed_conflict
            + 5 * self.temporary_norm
            + 5 * self.ghost_norm
        )
        return min(100, max(0, int(score)))

    def level(self) -> str:
        score = self.total_score()
        if score <= 33:
            return "low"
        elif score <= 66:
            return "mid"
        else:
            return "high"


class RiskAssessor:
    """Оцінка ризику норми (0-100)."""

    def __init__(self, db: Session):
        self.db = db

    def assess_provision(self, provision_id: str) -> dict[str, Any]:
        provision = self.db.query(LegalProvision).filter(LegalProvision.id == provision_id).first()
        if not provision:
            return {"error": "Provision not found"}

        factors = RiskFactors()

        # Check for sanctions in text
        text = provision.text or ""
        if re.search(r"штраф|штрафу|штрафом", text, re.IGNORECASE):
            factors.sanction_severity = 0.6
        if re.search(r"позбавлення волі|обмеження волі|криміналь", text, re.IGNORECASE):
            factors.sanction_severity = 1.0
        if re.search(r"попередження", text, re.IGNORECASE):
            factors.sanction_severity = 0.3

        # Check for deadlines
        if re.search(r"протягом \d+ дн", text, re.IGNORECASE):
            factors.deadline_proximity = 0.5

        # Check for ambiguity words
        ambiguity_words = ["розумний строк", "за потреби", "інші", "тощо", "негайно"]
        ambiguity_count = sum(1 for w in ambiguity_words if w in text.lower())
        factors.ambiguity = min(1.0, ambiguity_count * 0.2)

        # Check for temporary norms
        if re.search(r"на період дії воєнного стану|тимчасово", text, re.IGNORECASE):
            factors.temporary_norm = 1.0

        # Check for recent changes
        revision = self.db.query(DocumentRevision).filter(
            DocumentRevision.id == provision.document_revision_id
        ).first()
        if revision and revision.effective_from:
            from datetime import UTC, datetime, timedelta
            if revision.effective_from > datetime.now(UTC).date() - timedelta(days=90):
                factors.recent_change = 1.0

        return {
            "provision_id": provision_id,
            "score": factors.total_score(),
            "level": factors.level(),
            "factors": {
                "sanction_severity": factors.sanction_severity,
                "fine_size": factors.fine_size,
                "deadline_proximity": factors.deadline_proximity,
                "recent_change": factors.recent_change,
                "ambiguity": factors.ambiguity,
                "confirmed_conflict": factors.confirmed_conflict,
                "temporary_norm": factors.temporary_norm,
                "ghost_norm": factors.ghost_norm,
            },
        }
