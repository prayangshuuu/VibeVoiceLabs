"""Optional API key guard via X-API-Key (set API_KEY in the environment)."""

from __future__ import annotations

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        expected = os.environ.get("API_KEY", "").strip()
        if not expected:
            return await call_next(request)

        path = request.url.path
        if path in ("/", "/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"):
            return await call_next(request)
        if path.startswith("/audio/"):
            return await call_next(request)

        sent = request.headers.get("x-api-key", "")
        if sent != expected:
            return JSONResponse({"detail": "Invalid or missing API key (header: X-API-Key)"}, status_code=401)
        return await call_next(request)
