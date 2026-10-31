from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.services.connector import DataRadaConnector, ZakonRadaConnector, sync_once

router = APIRouter()


@router.post("/run")
async def run_sync(current_user=Depends(get_current_user)):
    if not current_user or not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
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
                "checksum": laws_list.get("checksum"),
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

    # Реальний Tier 1 імпорт: парсинг та збереження актів
    if check.reachable:
        try:
            import_result = await sync_once()
            results["import"] = import_result
        except Exception as exc:  # noqa: BLE001 — мережеві/БД помилки імпорту не повинні ламати відповідь
            results["import"] = {"error": str(exc), "stats": {}}

    return results


@router.get("/status")
async def sync_status():
    return {"connectors": ["data.rada.gov.ua", "zakon.rada.gov.ua"], "note": "sync status endpoint (MVP)"}
