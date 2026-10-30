"""
Тести авторизації (ТЗ, Крок К1 / А4, Крок К7).
Перевіряємо:
- без токена отримуємо 401, коли AUTH_DISABLED=False (за замовчуванням)
- реєстрація користувача
- логін (JWT) з правильним і неправильним паролем
- оновлення токена (refresh)
- доступ до захищеного ендпоінта з валідним токеном
- доступ до ендпоінта з невірним токеном
"""
import os
import time

# Використовуємо SQLite in-memory замість PostgreSQL для тестів
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base
from app.main import app

# Створюємо SQLite engine для тестів
_test_engine = create_engine("sqlite:///./test_auth.db", connect_args={"check_same_thread": False})
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Імпортуємо всі моделі для реєстрації в Base.metadata
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


def _unique_email(base: str) -> str:
    return f"{int(time.time() * 1000)}-{base}"


def test_stats_401_without_token() -> None:
    """Запит без токена до захищеного ендпоінта /api/v1/stats має повертати 401."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 401, response.text


def test_documents_401_without_token() -> None:
    """Запит без токена до /api/v1/documents має повертати 401."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 401, response.text


def test_register_success() -> None:
    """Реєстрація нового користувача успішна."""
    email = _unique_email("test@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == email
    assert "id" in data


def test_register_duplicate() -> None:
    """Реєстрація з існуючим email повертає 400."""
    email = _unique_email("dup@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 400, response.text


def test_login_success() -> None:
    """Логін з правильними даними повертає валідний JWT токен."""
    email = _unique_email("login@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "secret123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password() -> None:
    """Логін з неправильним паролем повертає 400."""
    email = _unique_email("wrong@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "wrongpassword"},
    )
    assert response.status_code == 400, response.text


def test_login_nonexistent_user() -> None:
    """Логін неіснуючого користувача повертає 400."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": _unique_email("nonexistent@example.com"), "password": "secret123"},
    )
    assert response.status_code == 400, response.text


def test_refresh_token() -> None:
    """Оновлення токена повертає новий валідний JWT."""
    email = _unique_email("refresh@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "secret123"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_protected_endpoint_with_token() -> None:
    """Захищений ендпоінт доступний з валідним токеном."""
    email = _unique_email("protected@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123"},
    )
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "secret123"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_protected_endpoint_with_invalid_token() -> None:
    """Захищений ендпоінт недоступний з невірним токеном."""
    response = client.get(
        "/api/v1/stats",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401, response.text
