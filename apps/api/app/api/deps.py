from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

reusable_oauth2 = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
):
    # Auth disabled (dev default): allow anonymous admin access.
    if (settings.AUTH_DISABLED or settings.APP_ENV == "development") and credentials is None:
        return {"id": "dev-user", "email": "dev@aiugoda.local", "is_superuser": True, "role": "admin"}
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = credentials.credentials
    # Reject default secret in production
    if settings.APP_ENV == "production" and token == "dev-secret-change-me":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SECRET_KEY")
    if settings.APP_ENV == "production" and token != settings.SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    # In non-production with auth enabled, accept the configured secret as a simple token.
    if not settings.AUTH_DISABLED and token != settings.SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return {"id": "dev-user", "email": "dev@aiugoda.local", "is_superuser": True, "role": "admin"}
