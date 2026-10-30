from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' http://localhost:8000 ws://localhost:8000; "
        "frame-ancestors 'none';"
    )
    return response

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
