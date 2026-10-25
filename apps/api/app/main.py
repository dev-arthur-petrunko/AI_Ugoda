from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Ukrainian Legal Intelligence Platform",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/", tags=["root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
    }