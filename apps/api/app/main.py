from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.middleware.rate_limit import RateLimitMiddleware

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
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def _startup_checks() -> None:
    if settings.APP_ENV == "production":
        if settings.SECRET_KEY == "dev-secret-change-me":
            raise RuntimeError("SECRET_KEY must be changed in production")
        if settings.AUTH_DISABLED:
            raise RuntimeError("AUTH_DISABLED must be false in production")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.APP_ENV, "auth_disabled": settings.AUTH_DISABLED}


@app.get("/", tags=["root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
    }
