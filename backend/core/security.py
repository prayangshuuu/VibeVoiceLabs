"""Auth helpers shared by HTTP and WebSocket."""

from __future__ import annotations

import os
from typing import Iterable

from starlette.requests import Request


def expected_api_key() -> str:
    return os.environ.get("API_KEY", "").strip()


def is_public_path(path: str, extra_public: Iterable[str] = ()) -> bool:
    """Paths that skip API key when API_KEY is set."""
    base = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }
    if path in base or path in extra_public:
        return True
    if path.startswith("/audio/"):
        return True
    # Versioned health for probes
    if path.endswith("/health") and "/api/v1" in path:
        return True
    return False


def validate_api_key_header(request: Request) -> bool:
    exp = expected_api_key()
    if not exp:
        return True
    return request.headers.get("x-api-key", "") == exp


def validate_api_key_ws(headers: dict, query_params: dict) -> bool:
    exp = expected_api_key()
    if not exp:
        return True
    h = headers.get("x-api-key") or query_params.get("api_key") or ""
    return h == exp
