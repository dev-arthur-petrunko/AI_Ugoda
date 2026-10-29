from fastapi import APIRouter

from app.api.v1.endpoints import analysis, auth, conflicts, diff, documents, graph, health, stats, sync

api_router = APIRouter()
api_router.include_router(health.router, prefix='/health', tags=['health'])
api_router.include_router(documents.router, prefix='/documents', tags=['documents'])
api_router.include_router(sync.router, prefix='/sync', tags=['synchronization'])
api_router.include_router(stats.router, prefix='/stats', tags=['stats'])
api_router.include_router(analysis.router, prefix="/documents", tags=["analysis"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(diff.router, prefix="/documents", tags=["diff"])
api_router.include_router(conflicts.router, prefix="/conflicts", tags=["conflicts"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])