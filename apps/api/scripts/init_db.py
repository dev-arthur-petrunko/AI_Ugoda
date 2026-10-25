"""Ініціалізація бази даних (створення всіх таблиць) для локального запуску."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, engine
from app.models import *

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Database tables created successfully")