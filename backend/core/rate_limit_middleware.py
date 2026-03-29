"""Apply RPM limits to TTS HTTP endpoints."""

from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

LIMITED_PREFIXES = ("/tts", "/api/v1/tts")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if request.method != "POST" or not any(path == p or path.startswith(p + "/") for p in LIMITED_PREFIXES):
            return await call_next(request)

        limiter = getattr(request.app.state, "rate_limiter", None)
        settings = getattr(request.app.state, "settings", None)
        if limiter is None or settings is None or settings.rate_limit_rpm <= 0:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        if not limiter.allow(client):
            return JSONResponse(
                {"detail": "Rate limit exceeded (requests per minute)", "code": "rate_limited"},
                status_code=429,
            )
        return await call_next(request)
