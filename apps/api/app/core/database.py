from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

# Resolve absolute DB path (works from any working directory)
_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite:///"):
    # Convert relative sqlite path to absolute
    rel = _db_url.replace("sqlite:///", "")
    abs_path = Path(rel).resolve()
    _db_url = f"sqlite:///{abs_path}"

connect_args = {}
if "sqlite" in _db_url:
    connect_args["check_same_thread"] = False

engine = create_engine(
    _db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()