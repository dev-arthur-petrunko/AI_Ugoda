"""AI service (TZ v2, розділ B.9 — RAG-конвеєр)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_provision import LegalProvision


@dataclass
class Citation:
    provision_id: str
    quote: str
    verified: bool = False


@dataclass
class AskResult:
    answer: str
    key_points: list[str]
    citations: list[Citation]
    confidence: float
    warnings: list[str]
    provider: str = field(default="mock")


class AIService:
    """Сервіс ШІ для роботи з законодавством (RAG).

    Підтримує провайдери: mock (за замовчуванням), groq, openai, anthropic.
    Кожна відповідь містить цитування з посиланням на статті законодавства.
    """

    def __init__(self, db: Session, provider: str | None = None):
        self.db = db
        self.provider = provider or settings.AI_PROVIDER

    # ------------------------------------------------------------------
    # Публічний API
    # ------------------------------------------------------------------

    def ask(self, question: str, document_id: str | None = None) -> AskResult:
        """Відповідає на питання з цитуванням статей (RAG)."""
        # 1. Пошук кандидатів
        from app.services.search import SearchService

        search = SearchService(self.db)
        results, _ = search.search(question, limit=10)

        # 2. Збір контексту з знайдених положень
        context_provisions = []
        for r in results:
            if r.revision_id:
                prov = (
                    self.db.query(LegalProvision)
                    .filter(LegalProvision.document_revision_id == r.revision_id)
                    .first()
                )
                if prov:
                    context_provisions.append(prov)

        if not context_provisions:
            return AskResult(
                answer="У базі не знайдено підтверджених норм. Перевірте на zakon.rada.gov.ua.",
                key_points=[],
                citations=[],
                confidence=0.0,
                warnings=["Джерело не знайдено"],
                provider=self.provider,
            )

        # 3. Генеруємо відповідь через обраний провайдер
        context_text = self._build_context(context_provisions)

        if self.provider == "mock":
            return self._mock_answer(question, context_provisions, context_text)

        try:
            if self.provider == "groq":
                answer = self._call_groq(question, context_text)
            elif self.provider == "openai":
                answer = self._call_openai(question, context_text)
            elif self.provider == "anthropic":
                answer = self._call_anthropic(question, context_text)
            else:
                answer = self._mock_answer(question, context_provisions, context_text).answer
        except Exception as exc:  # noqa: BLE001 — fallback на mock у разі помилки
            answer = f"Помилка провайдера {self.provider}: {exc}. (Використано fallback mock)"
            return self._mock_answer(question, context_provisions, context_text)

        # 4. Формуємо цитування
        citations = []
        for prov in context_provisions[:3]:
            citations.append(
                Citation(
                    provision_id=str(prov.id),
                    quote=(prov.text[:200] if prov.text else ""),
                    verified=True,
                )
            )

        return AskResult(
            answer=answer,
            key_points=self._extract_key_points(answer),
            citations=citations,
            confidence=0.85,
            warnings=[],
            provider=self.provider,
        )

    def summarize_act(self, document_id: str) -> dict[str, Any]:
        """Зведений опис акта (A1)."""
        doc = self.db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
        if not doc:
            return {"error": "Document not found"}

        revisions = (
            self.db.query(DocumentRevision)
            .filter(DocumentRevision.legal_document_id == doc.id)
            .all()
        )

        provisions = []
        for rev in revisions:
            provs = (
                self.db.query(LegalProvision)
                .filter(LegalProvision.document_revision_id == rev.id)
                .all()
            )
            provisions.extend(provs)

        summary_text = ""
        if self.provider != "mock" and provisions:
            context = self._build_context(provisions[:10])
            try:
                if self.provider == "groq":
                    summary_text = self._call_groq(
                        f"Зведіть короткий опис цього законодавчого акта: {doc.title}\n\nКонтекст: {context}",
                        context,
                    )
                elif self.provider == "openai":
                    summary_text = self._call_openai(
                        f"Зведіть короткий опис цього законодавчого акта: {doc.title}\n\nКонтекст: {context}",
                        context,
                    )
                elif self.provider == "anthropic":
                    summary_text = self._call_anthropic(
                        f"Зведіть короткий опис цього законодавчого акта: {doc.title}\n\nКонтекст: {context}",
                        context,
                    )
            except Exception:  # noqa: BLE001
                summary_text = ""

        if not summary_text:
            summary_text = (
                f"Акт містить {len(provisions)} положень у {len(revisions)} редакціях. "
                "(Мок-опис — підключіть реальний AI-провайдер для повного зведення.)"
            )

        return {
            "document_id": document_id,
            "title": doc.title,
            "status": doc.current_known_status,
            "revisions_count": len(revisions),
            "provisions_count": len(provisions),
            "summary": summary_text,
            "key_points": [f"Редакцій: {len(revisions)}", f"Положень: {len(provisions)}"],
            "provider": self.provider,
        }

    def verify_citation(self, provision_id: str, quote: str) -> bool:
        """Перевіряє, що цитата реально є в тексті положення."""
        provision = self.db.query(LegalProvision).filter(LegalProvision.id == provision_id).first()
        if not provision or not provision.text:
            return False
        normalized_text = provision.text.strip().lower()
        normalized_quote = quote.strip().lower()
        return normalized_quote in normalized_text

    # ------------------------------------------------------------------
    # Внутрішні методи
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(provisions: list[LegalProvision]) -> str:
        """Формує текстовий контекст зі знайдених положень для LLM."""
        parts = []
        for i, prov in enumerate(provisions, 1):
            heading = prov.heading or "Без заголовка"
            text = prov.text or ""
            parts.append(f"[Норма {i}] {heading}\n{text[:1500]}\n")
        return "\n".join(parts)

    @staticmethod
    def _mock_answer(
        question: str, provisions: list[LegalProvision], context_text: str
    ) -> AskResult:
        """Мок-відповідь (за замовчуванням, без реального LLM)."""
        citations = []
        for prov in provisions[:3]:
            citations.append(
                Citation(
                    provision_id=str(prov.id),
                    quote=(prov.text[:100] if prov.text else ""),
                    verified=True,
                )
            )
        return AskResult(
            answer=f"Знайдено {len(provisions)} релевантних норм. (Mock відповідь — потрібен реальний LLM провайдер)",
            key_points=[f"Знайдено {len(provisions)} норм"],
            citations=citations,
            confidence=0.5,
            warnings=["Mock-відповідь — потрібен реальний LLM провайдер"],
            provider="mock",
        )

    @staticmethod
    def _extract_key_points(answer: str) -> list[str]:
        """Витягує ключові пункти з тексту відповіді (простий спосіб)."""
        lines = [l.strip() for l in answer.split("\n") if l.strip()]
        return lines[:5] if lines else []

    # ------------------------------------------------------------------
    # Провайдери
    # ------------------------------------------------------------------

    def _call_groq(self, question: str, context: str) -> str:
        """Виклик Groq API."""
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise RuntimeError("GROQ_API_KEY не настроєно")
        model = settings.GROQ_MODEL or "llama-3.1-8b-instant"
        system_prompt = (
            "Ви — юридичний асистент для законодавства України. "
            "Відповідайте лише на основі наданого контексту. "
            "Кожне твердження повинне мати посилання на статтю та акт. "
            "Якщо інформації немає в контексті, кажіть «не знайдено в базі». "
            "Не вигадуйте закони."
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Контекст (положення законодавства):\n{context}\n\nПитання: {question}",
                },
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
        }
        return self._http_post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            api_key,
            payload,
            extract=lambda data: data["choices"][0]["message"]["content"],
        )

    def _call_openai(self, question: str, context: str) -> str:
        """Виклик OpenAI API."""
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY не настроєно")
        model = settings.OPENAI_MODEL or "gpt-4o-mini"
        system_prompt = (
            "Ви — юридичний асистент для законодавства України. "
            "Відповідайте лише на основі наданого контексту. "
            "Кожне твердження повинне мати посилання на статтю та акт. "
            "Якщо інформації немає в контексті, кажіть «не знайдено в базі». "
            "Не вигадуйте закони."
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Контекст (положення законодавства):\n{context}\n\nПитання: {question}",
                },
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
        }
        return self._http_post_json(
            "https://api.openai.com/v1/chat/completions",
            api_key,
            payload,
            extract=lambda data: data["choices"][0]["message"]["content"],
        )

    def _call_anthropic(self, question: str, context: str) -> str:
        """Виклик Anthropic API."""
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY не настроєно")
        model = settings.ANTHROPIC_MODEL or "claude-3-haiku-20240307"
        system_prompt = (
            "Ви — юридичний асистент для законодавства України. "
            "Відповідайте лише на основі наданого контексту. "
            "Кожне твердження повинне мати посилання на статтю та акт. "
            "Якщо інформації немає в контексті, кажіть «не знайдено в базі». "
            "Не вигадуйте закони."
        )
        payload = {
            "model": model,
            "max_tokens": 1000,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": f"Контекст (положення законодавства):\n{context}\n\nПитання: {question}",
                },
            ],
        }
        return self._http_post_json(
            "https://api.anthropic.com/v1/messages",
            api_key,
            payload,
            extract=lambda data: data["content"][0]["text"],
            extra_headers={"anthropic-version": "2023-06-01"},
        )

    @staticmethod
    def _http_post_json(
        url: str,
        api_key: str,
        payload: dict[str, Any],
        extract: Any,
        extra_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> str:
        """Загальний POST запит до LLM API з обробкою помилок."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return extract(data)
