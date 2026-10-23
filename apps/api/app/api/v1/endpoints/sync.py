from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.connector import ZakonRadaConnector

router = APIRouter()


@router.post("/run")
async def run_sync(current_user=Depends(get_current_user)):
    connector = ZakonRadaConnector()
    result = await connector.sync_once()
    return result


@router.get("/status")
async def sync_status():
    return {"connector": "zakon.rada.gov.ua", "note": "sync status endpoint (MVP)"}