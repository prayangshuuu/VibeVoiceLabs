from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/metrics")
def prometheus_friendly_metrics(request: Request):
    settings = request.app.state.settings
    if not settings.metrics_enabled:
        return {"enabled": False}
    m = request.app.state.metrics
    q = request.app.state.job_queue.queue_size
    return m.snapshot(queue_size=q)
