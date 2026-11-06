from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.services.connector import (
    DataRadaConnector,
    ImportAlreadyRunning,
    ZakonRadaConnector,
    import_locked,
    sync_once,
)

router = APIRouter()


async def _run_sync_background():
    """S3.3: імпорт — фоновим завданням; звіт пишеться в import_run."""
    import logging

    logger = logging.getLogger("aiugoda.import")
    try:
        await sync_once()
    except ImportAlreadyRunning as exc:
        # конкуруючий запуск відхилено блокуванням (див. /sync/run) — логується, не глушиться
        logger.warning("Фоновий імпорт відхилено: %s", exc)
    except Exception:
        # кожна помилка логується (правило: жодних «тихих» except)
        logger.exception("Фоновий імпорт завершився з помилкою")


@router.post("/run")
async def run_sync(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    if not current_user or not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    if import_locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Імпорт уже запущено (одночасно лише один запуск)",
        )

    results = {}

    data_connector = DataRadaConnector()
    try:
        check = await data_connector.check_source()
        results["data_rada"] = {
            "source": data_connector.base_url,
            "source_check": {
                "reachable": check.reachable,
                "status_code": check.status_code,
                "content_type": check.content_type,
                "note": check.note,
            },
        }
        if check.reachable:
            laws_list = await data_connector.fetch_laws_list()
            results["data_rada"]["laws_list"] = {
                "verified": laws_list.get("verified", False),
                "checksum": laws_list.get("content_sha256") or laws_list.get("checksum"),
                "cached": laws_list.get("cached", False),
                "note": laws_list.get("note"),
                "item_count": len(laws_list.get("data", {}).get("item", [])) if laws_list.get("data") else 0,
            }
    finally:
        await data_connector.close()

    zakon_connector = ZakonRadaConnector()
    try:
        check = await zakon_connector.check_source()
        results["zakon_rada"] = {
            "source": zakon_connector.base_url,
            "source_check": {
                "reachable": check.reachable,
                "status_code": check.status_code,
                "content_type": check.content_type,
                "note": check.note,
            },
        }
    finally:
        await zakon_connector.close()

    # Реальний Tier 1 імпорт: фоновим завданням (план S3, 3.3)
    if check.reachable:
        background_tasks.add_task(_run_sync_background)
        results["import"] = {"started": True, "mode": "background", "note": "див. GET /sync/runs"}

    return results


@router.get("/runs")
async def list_sync_runs(limit: int = 10):
    """S3.3: журнал запусків імпорту (import_run)."""
    from app.core.database import SessionLocal
    from app.models.import_run import ImportRun

    db = SessionLocal()
    try:
        rows = (
            db.query(ImportRun)
            .order_by(ImportRun.started_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "items": [
                {
                    "id": r.id,
                    "source": r.source,
                    "status": r.status,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                    "added": r.added,
                    "updated": r.updated,
                    "skipped": r.skipped,
                    "errors": r.errors,
                    "report": r.report_json,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.get("/status")
async def sync_status():
    from app.services.source_guard import source_statuses

    return {
        "connectors": ["data.rada.gov.ua", "zakon.rada.gov.ua"],
        "import_locked": import_locked(),
        "sources": source_statuses(),
    }
