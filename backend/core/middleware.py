"""Global HTTP middleware: request id, timing, logging."""

from __future__ import annotations

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.logging import get_logger
from core.tracing import new_trace_id, reset_trace_context, set_trace_id

logger = get_logger("vibevoice.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID, bind trace id, log latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("x-request-id") or new_trace_id()
        set_trace_id(rid)
        request.state.request_id = rid
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            reset_trace_context()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        response.headers["X-Request-ID"] = rid
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "%s %s -> %s in %.2fms",
            request.method,
            request.url.path,
            getattr(response, "status_code", "?"),
            elapsed_ms,
            extra={"request_id": rid},
        )
        return response


def ensure_request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = str(uuid.uuid4())
        request.state.request_id = rid
    return rid
