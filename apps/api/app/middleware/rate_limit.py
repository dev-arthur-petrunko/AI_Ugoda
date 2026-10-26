"""Rate limiting middleware (per client IP).

Uses Redis when available (REDIS_URL), with an in-memory fallback so the
service keeps working without Redis (e.g. local dev / tests). Sliding
window of 60 seconds, limit configurable via settings.RATE_LIMIT_PER_MINUTE.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

EXEMPT_PATHS = {"/health", "/", "/docs", "/openapi.json", "/redoc"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int | None = None) -> None:
        super().__init__(app)
        self.limit = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._redis = None
        redis_url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio as redis_async

                self._redis = redis_async.from_url(redis_url, decode_responses=True)
            except Exception:  # noqa: BLE001
                self._redis = None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        allowed = await self._allow(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)

    async def _allow(self, client_ip: str) -> bool:
        key = f"rl:{client_ip}"
        if self._redis is not None:
            try:
                now = time.time()
                window = 60.0
                pipe = self._redis.pipeline()
                pipe.zremrangebyscore(key, 0, now - window)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, 61)
                results = await pipe.execute()
                count_before = results[1]
                if count_before >= self.limit:
                    await self._redis.zrem(key, str(now))
                    return False
                return True
            except Exception:  # noqa: BLE001, S110
                pass

        now = time.time()
        window = 60.0
        bucket = self._buckets[client_ip]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True
