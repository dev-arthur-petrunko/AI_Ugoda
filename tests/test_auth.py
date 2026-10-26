"""
Тести авторизації (ТЗ, Крок К1 / А4).
Перевіряємо, що без токена отримуємо 401, коли AUTH_DISABLED=False (за замовчуванням).
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_stats_401_without_token() -> None:
    """Запит без токена до захищеного ендпоінта /api/v1/stats має повертати 401."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 401, response.text


def test_documents_401_without_token() -> None:
    """Запит без токена до /api/v1/documents має повертати 401."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 401, response.text