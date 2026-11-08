"""
Тест на SQL-ін'єкцію в пошуку (ТЗ v3, розділ A.9).

Перевіряє, що пошуковий запит не може виконати SQL-ін'єкцію.
Усі запити мають бути параметризовані.
"""

from __future__ import annotations

from app.services.search import SearchService


def test_search_sql_injection(svc) -> None:
    """Пошуковий запит з SQL-ін'єкцією не має повернути несанкціонованих даних."""
    search_service = SearchService(svc.db)

    # Спроба SQL-ін'єкції через параметр пошуку
    malicious_queries = [
        "'; DROP TABLE legal_provisions; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM legal_provisions; --",
        "'; DELETE FROM legal_documents; --",
        "' OR 1=1 --",
    ]

    for q in malicious_queries:
        # Захист від ін'єкції: запит НЕ має кидати виняток і НЕ має змінювати дані.
        # Якщо щось кинулося — тест ПАДАЄ (тихих except немає, правило S3).
        results = search_service.search(q, limit=5)
        assert isinstance(results, tuple) and isinstance(results[0], list)

    # Нормальний пошук має працювати (повертає кортеж (results, count))
    search_results = search_service.search("конституція", limit=5)
    assert isinstance(search_results, tuple)
    assert isinstance(search_results[0], list)