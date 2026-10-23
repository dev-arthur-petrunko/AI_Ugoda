from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.connector import DataRadaConnector, ZakonRadaConnector

router = APIRouter()


@router.post("/run")
async def run_sync(current_user=Depends(get_current_user)):
    """Запускає синхронізацію з обох джерел (data.rada.gov.ua основне, zakon.rada.gov.ua запасне)."""
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

    return results


@router.get("/status")
async def sync_status():
    return {"connectors": ["data.rada.gov.ua", "zakon.rada.gov.ua"], "note": "sync status endpoint (MVP)"}