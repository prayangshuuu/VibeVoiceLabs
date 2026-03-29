"""Attach request latency and error counts to the metrics registry."""

from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        metrics = getattr(request.app.state, "metrics", None)
        settings = getattr(request.app.state, "settings", None)
        if metrics is None or settings is None or not settings.metrics_enabled:
            return await call_next(request)

        t0 = time.perf_counter()
        error = False
        try:
            response = await call_next(request)
            error = response.status_code >= 500
            return response
        except Exception:
            error = True
            raise
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            metrics.record_request(latency_ms, error=error)
