from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/metrics")
def prometheus_friendly_metrics(request: Request):
    settings = request.app.state.settings
    if not settings.metrics_enabled:
        return {"enabled": False}
    m = request.app.state.metrics
    cluster = getattr(request.app.state, "cluster_supervisor", None)
    jq = getattr(request.app.state, "job_queue", None)
    if cluster is not None:
        q = cluster.queue_depth
    elif jq is not None:
        q = jq.queue_size
    else:
        q = 0
    return m.snapshot(queue_size=q)
