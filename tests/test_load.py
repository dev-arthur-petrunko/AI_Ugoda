"""Навантажувальні тести (K12 — якість).
Симулюємо паралельні запити до API для перевірки стабільності під навантаженням.
"""
from __future__ import annotations

import concurrent.futures
import os
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_load.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base
from app.main import app

_test_engine = create_engine("sqlite:///./test_load.db", connect_args={"check_same_thread": False})
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

from app.models import (  # noqa: F401
    LegalDocument, DocumentRevision, LegalProvision, LegalEvent,
    LegalReference, LegalLink, LegalForceLevel, AIAnalysis,
    ConflictCandidate, User, UserMonitoringRule, UserBookmark,
    ContractDocument, ContractAnalysis, AuditLog,
)

Base.metadata.create_all(bind=_test_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)


def _health_request(_: int) -> int:
    resp = client.get("/health")
    return resp.status_code


def test_concurrent_health_requests() -> None:
    """50 паралельних запитів до /health — всі повинні успішні."""
    n = 50
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(_health_request, range(n)))
    assert all(r == 200 for r in results), f"Не всі записи успішні: {results}"


def test_sequential_health_requests() -> None:
    """100 послідовних запитів до /health — всі повинні успішні."""
    for _ in range(100):
        resp = client.get("/health")
        assert resp.status_code == 200


def test_response_time_under_load() -> None:
    """Час відповіді під навантаженням не перевищує 2 секунди на запит."""
    n = 30
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(_health_request, range(n)))
    elapsed = time.perf_counter() - start
    avg_per_request = elapsed / n
    assert avg_per_request < 2.0, f"Середній час занадто високий: {avg_per_request:.3f}s"
