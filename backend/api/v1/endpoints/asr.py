from __future__ import annotations

import time

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from core.middleware import ensure_request_id
from schemas.common import ApiMeta, ApiResponse
from services.asr_pipeline import run_asr

router = APIRouter()


@router.post("/asr")
async def post_asr_v1(
    request: Request,
    file: UploadFile = File(..., description="Audio file (any common format; mock ASR ignores codec)"),
):
    rid = ensure_request_id(request)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio upload")
    mm = getattr(request.app.state, "model_manager", None)
    if mm is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    cluster = getattr(request.app.state, "cluster_supervisor", None)
    t0 = time.perf_counter()
    try:
        result = await run_asr(
            model_manager=mm,
            cluster_supervisor=cluster,
            audio_bytes=data,
            filename=file.filename,
            request_id=rid,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR failed: {e}") from e

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return ApiResponse(
        request_id=rid,
        status="success",
        data=result,
        meta=ApiMeta(
            latency_ms=round(elapsed_ms, 3),
            engine=str(result.get("model", "asr")),
            strategy="cluster" if cluster else "inline",
        ),
    )
