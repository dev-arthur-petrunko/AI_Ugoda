"""§4.3: backfill legal_links + legal_events з уже імпортованих редакцій.

Запуск: python scripts/extract_links.py
Ідемпотентно: повторний запуск не дублює записи (дедуп у build_links_for_revision).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.services.import_service import ImportService


def main() -> int:
    db = SessionLocal()
    try:
        svc = ImportService(db)
        docs = db.query(LegalDocument).all()
        total_links = 0
        total_events = 0
        for doc in docs:
            # Беремо ревізію з найбільшою кількістю положень (як у /quality).
            revisions = (
                db.query(DocumentRevision)
                .filter(DocumentRevision.legal_document_id == doc.id)
                .all()
            )
            if not revisions:
                continue
            best = max(
                revisions,
                key=lambda r: sum(1 for p in r.provisions if p.text),
            )
            stats = svc.build_links_for_revision(best, doc)
            total_links += stats["links"]
            total_events += stats["events"]
            print(
                f"{doc.source_id}: links +{stats['links']}, events +{stats['events']}",
                flush=True,
            )
        print(f"TOTAL: links +{total_links}, events +{total_events}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
