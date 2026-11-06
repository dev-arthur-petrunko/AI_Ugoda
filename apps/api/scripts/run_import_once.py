"""Одиничний запуск імпорту Tier 1 для приймання S3 (доказ)."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.connector import sync_once


async def main():
    result = await sync_once()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
