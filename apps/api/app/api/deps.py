from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

reusable_oauth2 = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
    db: Session = Depends(get_db),
) -> dict:
    """
    Поточний автентифікований користувач.

    У dev-режимі з AUTH_DISABLED=True дозволяє анонімний доступ без прав адміна.
    У інших випадках вимагає валідний JWT токен, шукає користувача в БД за email (sub).
    """
    # Auth disabled (dev default): allow anonymous access WITHOUT admin rights.
    if settings.AUTH_DISABLED and settings.APP_ENV == "development" and credentials is None:
        return {
            "id": "dev-user",
            "email": "dev@aiugoda.local",
            "is_superuser": False,
            "role": "user",
            "is_active": True,
        }

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "is_superuser": user.is_superuser,
        "role": "admin" if user.is_superuser else "user",
        "is_active": user.is_active,
    }


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Користувач має бути активним."""
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_current_superuser(current_user: dict = Depends(get_current_user)) -> dict:
    """Тільки для суперкористувачів (адмінів)."""
    if not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
