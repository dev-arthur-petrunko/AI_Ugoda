
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.search import SearchFilters, SearchService

router = APIRouter()


@router.get("")
async def list_documents(
    q: str | None = Query(None, description="Пошуковий запит (назва/текст/номер)"),
    document_type: str | None = Query(None, description="Тип документа"),
    status: str | None = Query(None, description="Статус документа"),
    issuing_authority: str | None = Query(None, description="Орган, що видав"),
    adoption_date_from: str | None = Query(None, description="Дата прийняття від (YYYY-MM-DD)"),
    adoption_date_to: str | None = Query(None, description="Дата прийняття до (YYYY-MM-DD)"),
    legal_force_level: str | None = Query(None, description="Рівень юридичної сили"),
    include_fixtures: bool = Query(False, description="Включити тестові акти (fixture); за замовчуванням лише official"),
    only_current: bool = Query(True, description="Тільки актуальні редакції"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    # Публічне читання без авторизації (K5 / план §5.3); запис — тільки з токеном.
):
    search_service = SearchService(db)
    filters = SearchFilters(
        document_type=document_type,
        status=status,
        issuing_authority=issuing_authority,
        adoption_date_from=adoption_date_from,
        adoption_date_to=adoption_date_to,
        legal_force_level=legal_force_level,
        include_fixtures=include_fixtures,
        only_current=only_current,
    )
    items, total = search_service.search(q or "", filters, limit, offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": item.id,
                "source_id": item.source_id,
                "title": item.title,
                "document_type": item.document_type,
                "document_number": item.document_number,
                "adoption_date": item.adoption_date,
                "issuing_authority": item.issuing_authority,
                "current_known_status": item.current_known_status,
                "source_url": item.source_url,
                "revision_id": item.revision_id,
                "revision_date": item.revision_date,
                "data_origin": item.data_origin,
            }
            for item in items
        ],
    }


@router.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=2, description="Часткова назва для автозаповнення"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    # Публічне читання без авторизації (K5 / план §5.3); запис — тільки з токеном.
):
    search_service = SearchService(db)
    suggestions = search_service.get_suggestions(q, limit)
    return {"suggestions": suggestions}


@router.get("/search/by-provision")
async def search_by_provision(
    provision_ref: str = Query(..., description="Посилання на статтю (напр. 'Стаття 15')"),
    db: Session = Depends(get_db),
    # Публічне читання без авторизації (K5 / план §5.3); запис — тільки з токеном.
):
    search_service = SearchService(db)
    items = search_service.search_by_provision(provision_ref)
    return {
        "items": [
            {
                "id": item.id,
                "source_id": item.source_id,
                "title": item.title,
                "document_type": item.document_type,
                "document_number": item.document_number,
                "adoption_date": item.adoption_date,
                "issuing_authority": item.issuing_authority,
                "current_known_status": item.current_known_status,
                "source_url": item.source_url,
                "revision_id": item.revision_id,
                "revision_date": item.revision_date,
                "matched_provision": item.matched_provision,
            }
            for item in items
        ],
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    # Публічне читання без авторизації (K5 / план §5.3); запис — тільки з токеном.
):
    from app.models.document_revision import DocumentRevision
    from app.models.legal_document import LegalDocument
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Документ не знайдено")
    revisions = (
        db.query(DocumentRevision)
        .filter(DocumentRevision.legal_document_id == doc.id)
        .order_by(DocumentRevision.revision_date.desc().nullslast())
        .all()
    )
    return {
        "id": str(doc.id),
        "source_id": doc.source_id,
        "title": doc.title,
        "document_type": doc.document_type,
        "document_number": doc.document_number,
        "adoption_date": doc.adoption_date.isoformat() if doc.adoption_date else None,
        "issuing_authority": doc.issuing_authority,
        "current_known_status": doc.current_known_status,
        "source_url": doc.source_url,
        "source_metadata_json": doc.source_metadata_json,
        "data_origin": doc.data_origin,
        "revisions": [
            {
                "id": str(r.id),
                "revision_label": r.revision_label,
                "revision_date": r.revision_date.isoformat() if r.revision_date else None,
                "effective_from": r.effective_from.isoformat() if r.effective_from else None,
                "effective_to": r.effective_to.isoformat() if r.effective_to else None,
                "source_url": r.source_url,
                "source_checksum": r.source_checksum,
                "verification_status": r.verification_status,
            }
            for r in revisions
        ],
    }


@router.get("/{document_id}/quality")
async def document_quality(document_id: str, db: Session = Depends(get_db)):
    """S3.6 — картка «Якість розбору»: розібрано/очікується, прогалини, порожні статті, статус."""
    from fastapi import HTTPException
    from sqlalchemy import func

    from app.models.document_revision import DocumentRevision
    from app.models.legal_document import LegalDocument
    from app.models.legal_provision import LegalProvision

    doc = db.get(LegalDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не знайдено")

    # S3.6: обираємо ревізію з найбільшою кількістю положень
    # (модель не має is_current; ревізії з різним effective_from — різна повнота).
    best = (
        db.query(DocumentRevision.id, func.count(LegalProvision.id).label("n"))
        .outerjoin(LegalProvision, LegalProvision.document_revision_id == DocumentRevision.id)
        .filter(DocumentRevision.legal_document_id == doc.id)
        .group_by(DocumentRevision.id)
        .order_by(func.count(LegalProvision.id).desc())
        .first()
    )
    current_rev = db.get(DocumentRevision, best[0]) if best else None
    articles: list[tuple[int, str]] = []
    if current_rev:
        rows = (
            db.query(LegalProvision.article_number, LegalProvision.text)
            .filter(
                LegalProvision.document_revision_id == current_rev.id,
                LegalProvision.article_number.isnot(None),
            )
            .all()
        )
        for art_num, text in rows:
            try:
                articles.append((int(str(art_num)), (text or "").strip()))
            except ValueError:
                continue

    parsed_count = len({n for n, _ in articles})
    numbers = sorted({n for n, _ in articles})
    expected = max(numbers) if numbers else 0  # за останнім номером статті

    # §2.1 «виключені» статті визначаємо з тексту джерела (L1, без хардкоду):
    # 1) явні примітки «Стаття N … виключено»;
    # 2) пропуски у проміжку між наявними статтями, де джерело містить «виключено».
    import re as _re

    excluded: set[int] = set()
    gap_note = ""
    text_norm = (current_rev.normalized_text or "") if current_rev else ""
    if text_norm:
        for m in _re.finditer(r"[Сс]татт\w*\s+(\d+)(?:\s+частин\w*|\s+абзац\w*)?[^.]{0,150}?виключен", text_norm):
            try:
                excluded.add(int(m.group(1)))
            except ValueError:
                pass
        positions: dict[int, int] = {}
        for m in _re.finditer(r"[Сс]таття\s+(\d+)", text_norm):
            try:
                positions.setdefault(int(m.group(1)), m.start())
            except ValueError:
                pass
        present = set(numbers)
        for n in range(1, expected + 1):
            if n in present or n in excluded:
                continue
            prevs = [p for p in present if p < n]
            nexts = [p for p in present if p > n]
            if not prevs or not nexts:
                continue
            p, q = max(prevs), min(nexts)
            if p in positions and q in positions and positions[p] < positions[q]:
                seg = text_norm[positions[p]:positions[q]].lower()
                if "виключен" in seg:
                    excluded.add(n)
        if excluded:
            gap_note = (
                "Частина номерів позначена «виключено» в офіційному тексті — "
                "це не пропуски розбору (напр., виключений розділ Конституції)."
            )

    gaps_all = [n for n in range(1, expected + 1) if n not in set(numbers)]
    gaps = [n for n in gaps_all if n not in excluded]
    # «Виключено» показуємо лише для тих номерів, яких немає в розборі:
    # часткові виключення («Статтю N частину виключено») — стаття розібрана, пропуску немає.
    excluded_absent = sorted(n for n in excluded if n not in set(numbers))
    empty_articles = sorted({n for n, t in articles if not t})

    if parsed_count == 0 or expected and parsed_count < expected * 0.5:
        status = "quarantine"
    elif gaps or empty_articles:
        status = "warning"
    else:
        status = "ok"

    # Рівні виводимо з наявних колонок: provision_level у моделі немає.
    total_prov = articles_in_structure = 0
    if current_rev:
        total_prov = (
            db.query(LegalProvision.id)
            .filter(LegalProvision.document_revision_id == current_rev.id)
            .count()
        )
        articles_in_structure = (
            db.query(LegalProvision.id)
            .filter(
                LegalProvision.document_revision_id == current_rev.id,
                LegalProvision.article_number.isnot(None),
            )
            .count()
        )
    outside_pct = 0.0 if total_prov == 0 else round(100.0 * (total_prov - articles_in_structure) / total_prov, 1)

    return {
        "document_id": str(doc.id),
        "title": doc.title,
        "data_origin": doc.data_origin,
        "revision_id": str(current_rev.id) if current_rev else None,
        "parsed_articles": parsed_count,
        "expected_articles": expected,
        "gaps": gaps[:50],
        "gaps_count": len(gaps),
        "excluded_articles": excluded_absent[:50],
        "excluded_count": len(excluded_absent),
        "empty_articles": empty_articles[:50],
        "empty_count": len(empty_articles),
        "text_outside_structure_pct": outside_pct,
        "status": status,
        "note": gap_note or "quarantine не виходить у пошук; очікування Конституції — 161 стаття (звірити з джерелом)",
    }


@router.get("/{document_id}/provisions")
async def get_provisions(document_id: str, db: Session = Depends(get_db)):
    from app.models.document_revision import DocumentRevision
    from app.models.legal_document import LegalDocument
    from app.models.legal_provision import LegalProvision
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    rev = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).order_by(DocumentRevision.revision_date.desc().nullslast()).first()
    if not rev:
        return {"document_id": document_id, "revision_id": None, "items": []}
    provs = db.query(LegalProvision).filter(LegalProvision.document_revision_id == rev.id).order_by(LegalProvision.ordinal.asc().nullslast()).all()
    def node(p):
        return {"id": str(p.id), "parent_id": str(p.parent_provision_id) if p.parent_provision_id else None, "identifier": p.provision_identifier, "article_number": p.article_number, "heading": p.heading, "text": p.text, "ordinal": p.ordinal}
    return {"document_id": document_id, "revision_id": str(rev.id), "items": [node(p) for p in provs]}


@router.get("/{document_id}/revisions")
async def get_revisions(document_id: str, db: Session = Depends(get_db)):
    from app.models.document_revision import DocumentRevision
    from app.models.legal_document import LegalDocument
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    revisions = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).order_by(DocumentRevision.revision_date.desc().nullslast()).all()
    return {"document_id": document_id, "items": [{"id": str(r.id), "label": r.revision_label, "revision_date": r.revision_date.isoformat() if r.revision_date else None, "effective_from": r.effective_from.isoformat() if r.effective_from else None, "effective_to": r.effective_to.isoformat() if r.effective_to else None, "source_url": r.source_url, "verification_status": r.verification_status} for r in revisions]}


@router.get("/{document_id}/at")
async def get_at(document_id: str, date: str, db: Session = Depends(get_db)):
    from datetime import date as ddate

    from app.models.document_revision import DocumentRevision
    from app.models.legal_document import LegalDocument
    doc = db.get(LegalDocument, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    try:
        target = ddate.fromisoformat(date)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Невірний формат дати (YYYY-MM-DD)")
    revs = db.query(DocumentRevision).filter(DocumentRevision.legal_document_id == doc.id).all()
    chosen = None
    for r in revs:
        if r.effective_from and r.effective_from <= target and (r.effective_to is None or r.effective_to >= target):
            chosen = r
            break
    if chosen is None and revs:
        chosen = max(revs, key=lambda r: r.effective_from or ddate.min)
    if chosen is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Редакцію не знайдено")
    return {"document_id": document_id, "date": date, "revision_id": str(chosen.id), "effective_from": chosen.effective_from.isoformat() if chosen.effective_from else None, "effective_to": chosen.effective_to.isoformat() if chosen.effective_to else None}
