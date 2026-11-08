"""
Тестові фікстури для AI Ugoda (TZ v2).

Використовуємо SQLite in-memory для швидких юніт-тестів без реальної PostgreSQL.
"""
from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

import pytest

# Імпортуємо всі моделі, щоб вони зареєструвалися в Base.metadata
from app.models import (  # noqa: F401
    AIAnalysis,
    AuditLog,
    ConflictCandidate,
    ContractAnalysis,
    ContractDocument,
    DocumentRevision,
    LegalDocument,
    LegalEvent,
    LegalForceLevel,
    LegalLink,
    LegalProvision,
    LegalReference,
    User,
    UserBookmark,
    UserMonitoringRule,
)
from app.models.base import Base
from app.services.import_service import ImportService
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def svc(db: Session) -> Generator[ImportService, None, None]:
    with ImportService(db) as service:
        yield service