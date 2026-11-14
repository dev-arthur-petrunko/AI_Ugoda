"""Граф зв'язків акта з legal_links (§4.3: дані вже в базі).

Не стаб: вузли й ребра будуються з офіційних приміток джерела
(15 330 зв'язків), згрупованих по документах.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document_revision import DocumentRevision
from app.models.legal_document import LegalDocument
from app.models.legal_link import LegalLink
from app.models.legal_provision import LegalProvision

router = APIRouter()

# Типи зв'язків → підписи в UI.
LINK_LABELS: dict[str, str] = {
    "amends": "змінює",
    "repeals": "виключає/скасовує",
    "refers_to": "посилається",
    "implements": "реалізує",
    "interprets": "тлумачить",
    "harmonizes_with": "узгоджується",
}

DEFAULT_MAX_EDGES = 400


@router.get("/{document_id}")
async def get_graph(
    document_id: str,
    depth: int = 2,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Вузли/ребра графа для акта з legal_links (агрегація по документах).

    Ребро = (документ-джерело, документ-ціль, тип зв'язку); вага = кількість
    зв'язків. Нерозпізнані акти з приміток — окремі вузли «нема в каталозі».
    depth впливає лише на кількість «хопів» (1..3), поки граф плоский (багато
    на одному рівні).
    """
    if depth not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="depth має бути 1..3")

    root = db.get(LegalDocument, document_id)
    if not root:
        raise HTTPException(status_code=404, detail="Документ не знайдено")

    # Положення кореневого документа.
    root_prov_ids = [
        str(pid)
        for (pid,) in db.query(LegalProvision.id)
        .join(DocumentRevision, DocumentRevision.id == LegalProvision.document_revision_id)
        .filter(DocumentRevision.legal_document_id == document_id)
        .all()
    ]
    if not root_prov_ids:
        return {
            "document_id": document_id,
            "depth": depth,
            "nodes": [
                {"id": str(root.id), "label": root.title, "type": "document", "role": "root"}
            ],
            "edges": [],
            "found_by": "code",
        }

    # Вихідні зв'язки: положення документа → інші акти.
    # (Без GROUP BY за source_meta_json: тип json у PostgreSQL не має
    # оператора рівності — агрегуємо в пам'яті.)
    out_rows = (
        db.query(
            LegalLink.link_type,
            LegalLink.resolution_status,
            LegalLink.evidence_text,
            LegalLink.target_document_id,
            LegalLink.source_meta_json,
        )
        .filter(LegalLink.source_provision_id.in_(root_prov_ids))
        .all()
    )
    # Вхідні зв'язки: інші акти → положення документа.
    in_rows = (
        db.query(
            LegalLink.link_type,
            LegalLink.resolution_status,
            LegalLink.evidence_text,
            LegalProvision.document_revision_id,
        )
        .join(
            LegalProvision,
            LegalProvision.id == LegalLink.source_provision_id,
        )
        .filter(LegalLink.target_provision_id.in_(root_prov_ids))
        .all()
    )

    nodes: dict[str, dict] = {
        str(root.id): {
            "id": str(root.id),
            "label": root.title,
            "type": "document",
            "role": "root",
        }
    }
    # Ключ агрегації: (source, target, тип зв'язку).
    agg: dict[tuple, dict] = {}

    def _touch(key: tuple, row) -> None:
        slot = agg.setdefault(key, {"n": 0, "statuses": set(), "evidence": []})
        slot["n"] += 1
        slot["statuses"].add(row.resolution_status)
        if row.evidence_text and len(slot["evidence"]) < 3:
            slot["evidence"].append(row.evidence_text)

    root_id = str(root.id)
    for row in out_rows:
        meta = row.source_meta_json or {}
        target = str(row.target_document_id) if row.target_document_id else None
        if not target:
            # Нерозпізнаний акт — окремий вузол за номером із примітки.
            target = f"unresolved:{meta.get('act_number') or '?'}"
            nodes.setdefault(
                target,
                {
                    "id": target,
                    "label": f"Акт № {meta.get('act_number')} (нема в каталозі)",
                    "type": "document",
                    "role": "unresolved",
                },
            )
        _touch((root_id, target, row.link_type), row)

    # Вхідні: revision → документ.
    rev_ids = {str(r.document_revision_id) for r in in_rows if r.document_revision_id}
    rev_to_doc: dict[str, str] = {}
    if rev_ids:
        for rev_id, doc_id in db.query(DocumentRevision.id, DocumentRevision.legal_document_id).filter(
            DocumentRevision.id.in_(list(rev_ids))
        ):
            rev_to_doc[str(rev_id)] = str(doc_id)
    for row in in_rows:
        src = rev_to_doc.get(str(row.document_revision_id or ""))
        if not src:
            continue
        _touch((src, root_id, row.link_type), row)

    # Назви сусідніх документів.
    neighbor_ids = {k[1] if k[0] == root_id else k[0] for k in agg}
    real_ids = [i for i in neighbor_ids if not i.startswith("unresolved:")]
    if real_ids:
        for d in db.query(LegalDocument).filter(LegalDocument.id.in_(real_ids)).all():
            nodes[str(d.id)] = {
                "id": str(d.id),
                "label": d.title,
                "type": "document",
                "role": "neighbor",
            }

    edges: list[dict] = []
    for (src, tgt, ltype), info in agg.items():
        for nid in (src, tgt):
            nodes.setdefault(nid, {"id": nid, "label": nid, "type": "document", "role": "neighbor"})
        edges.append(
            {
                "source": src,
                "target": tgt,
                "type": ltype,
                "label": LINK_LABELS.get(ltype, ltype),
                "weight": info["n"],
                "resolved": "resolved" in info["statuses"],
                "evidence": info["evidence"][:1],
            }
        )
    edges.sort(key=lambda e: -e["weight"])
    edges = edges[:DEFAULT_MAX_EDGES]

    return {
        "document_id": document_id,
        "depth": depth,
        "nodes": list(nodes.values()),
        "edges": edges,
        "found_by": "code",  # L1: з офіційних приміток джерела, без ШІ
    }
