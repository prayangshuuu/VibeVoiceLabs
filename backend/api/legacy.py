"""Stable root paths for existing clients (Next.js dashboard, curl)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, WebSocket

from api.v1.endpoints.stream import stream_ws_v1
from api.v1.endpoints.tts import LegacyTTSResponse, TTSRequest, execute_tts
from api.v1.endpoints.voices import api_voices
from core.middleware import ensure_request_id

legacy_router = APIRouter(tags=["legacy"])


@legacy_router.get("/voices")
def legacy_voices(request: Request):
    return api_voices(request)


@legacy_router.post("/tts", response_model=LegacyTTSResponse)
async def legacy_tts(req: TTSRequest, request: Request):
    try:
        result, _elapsed_ms = await execute_tts(request, req)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}") from e

    ensure_request_id(request)
    from pathlib import Path

    p = Path(result.output_path)
    filename = p.name
    base = str(request.base_url).rstrip("/")
    return LegacyTTSResponse(
        filename=filename,
        output_path=str(result.output_path),
        audio_url=f"{base}/audio/{filename}",
        message="ok",
    )


@legacy_router.websocket("/stream")
async def legacy_stream_ws(websocket: WebSocket):
    await stream_ws_v1(websocket)
