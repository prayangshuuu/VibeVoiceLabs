from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.middleware import ensure_request_id
from core.tracing import span
from domain.models import InferenceResult
from schemas.common import ApiMeta, ApiResponse
from services.tts_pipeline import run_tts
from utils.speaker import assert_max_speakers

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Preset id, e.g. carter, emma")
    mode: Optional[str] = Field(
        None,
        description="UI preset: default, podcast, narration (optional; does not change model weights)",
    )
    cfg_scale: float = Field(1.5, ge=0.5, le=3.0)
    multi_speaker: bool = Field(
        False,
        description="If true, parse lines like 'A: Hello' / 'B: Hi' and map speakers to voices",
    )
    speaker_voices: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional map of speaker label -> voice id",
    )


class LegacyTTSResponse(BaseModel):
    filename: str
    output_path: str
    audio_url: str
    message: str = "ok"


async def execute_tts(request: Request, req: TTSRequest) -> Tuple[InferenceResult, float]:
    settings = request.app.state.settings
    if len(req.text) > settings.max_chars_per_request:
        raise HTTPException(
            status_code=400,
            detail=f"Text exceeds max length ({settings.max_chars_per_request} characters).",
        )
    if req.multi_speaker:
        try:
            assert_max_speakers(req.text, max_speakers=4)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    rid = ensure_request_id(request)
    t0 = time.perf_counter()
    with span("tts.pipeline", voice=req.voice, multi_speaker=req.multi_speaker):
        result = await run_tts(
            settings=settings,
            voice_manager=request.app.state.voice_manager,
            inference_router=request.app.state.inference_router,
            job_queue=getattr(request.app.state, "job_queue", None),
            cluster_supervisor=getattr(request.app.state, "cluster_supervisor", None),
            generation_cache=request.app.state.generation_cache,
            text=req.text,
            voice=req.voice,
            cfg_scale=req.cfg_scale,
            multi_speaker=req.multi_speaker,
            speaker_voice_map=req.speaker_voices,
            request_id=rid,
        )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return result, elapsed_ms


def _audio_payload(request: Request, result: InferenceResult) -> dict:
    p = Path(result.output_path)
    filename = p.name
    base = str(request.base_url).rstrip("/")
    return {
        "filename": filename,
        "output_path": str(result.output_path),
        "audio_url": f"{base}/audio/{filename}",
    }


@router.post("/tts")
async def post_tts_v1(req: TTSRequest, request: Request):
    rid = ensure_request_id(request)
    try:
        result, elapsed_ms = await execute_tts(request, req)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}") from e

    data = _audio_payload(request, result)
    return ApiResponse(
        request_id=rid,
        status="success",
        data=data,
        meta=ApiMeta(latency_ms=round(elapsed_ms, 3), engine=result.engine, strategy=result.strategy),
    )
