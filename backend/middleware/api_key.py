"""Optional API key guard via X-API-Key (set API_KEY in the environment)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.security import expected_api_key, is_public_path, validate_api_key_header


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not expected_api_key():
            return await call_next(request)

        path = request.url.path
        extra = ("/api/v1/health",)
        if is_public_path(path, extra_public=extra):
            return await call_next(request)

        if not validate_api_key_header(request):
            return JSONResponse({"detail": "Invalid or missing API key (header: X-API-Key)"}, status_code=401)
        return await call_next(request)
