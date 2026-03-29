from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/cluster/status")
def cluster_status(request: Request):
    sup = getattr(request.app.state, "cluster_supervisor", None)
    if sup is None:
        raise HTTPException(status_code=503, detail="Cluster supervisor not enabled")
    return sup.status_snapshot()
