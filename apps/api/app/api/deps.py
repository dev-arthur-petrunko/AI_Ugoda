from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.config import settings

reusable_oauth2 = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
):
    # MVP placeholder: real JWT verification is implemented in Phase 7/8.
    # Returns None when no credentials are provided (public read endpoints remain open).
    if credentials is None:
        return None
    token = credentials.credentials
    if token != settings.SECRET_KEY and settings.APP_ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"id": "dev-user", "email": "dev@aiugoda.local", "is_superuser": settings.APP_ENV != "production"}