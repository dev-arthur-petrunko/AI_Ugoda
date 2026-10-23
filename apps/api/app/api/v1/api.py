from fastapi import APIRouter

from app.api.v1.endpoints import health, documents, sync

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(sync.router, prefix="/sync", tags=["synchronization"])