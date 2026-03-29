"""WebSocket streaming TTS (incremental chunks + PCM frames)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.inference import synthesize_stream_pcm

router = APIRouter(tags=["stream"])


class StreamCommand(BaseModel):
    """One-shot synthesis (server chunks text and streams PCM)."""

    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    cfg_scale: float = Field(1.5, ge=0.5, le=3.0)


def _check_ws_api_key(websocket: WebSocket) -> bool:
    expected = os.environ.get("API_KEY", "").strip()
    if not expected:
        return True
    header = websocket.headers.get("x-api-key") or websocket.query_params.get("api_key") or ""
    return header == expected


@router.websocket("/stream")
async def stream_ws(websocket: WebSocket):
    await websocket.accept()
    if not _check_ws_api_key(websocket):
        await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid API key"}))
        await websocket.close(code=4401)
        return

    buf: List[str] = []

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload: Dict[str, Any] = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON"}))
                continue

            action = payload.get("action", "synthesize")

            if action == "reset":
                buf.clear()
                await websocket.send_text(json.dumps({"type": "progress", "stage": "reset", "message": "Buffer cleared"}))
                continue

            if action == "append_text":
                t = (payload.get("text") or "").strip()
                if t:
                    buf.append(t)
                await websocket.send_text(
                    json.dumps({"type": "progress", "stage": "buffer", "chars": sum(len(x) for x in buf), "demo": True})
                )
                continue

            if action == "synthesize":
                text = (payload.get("text") or "").strip()
                if not text and buf:
                    text = "\n".join(buf)
                if not text:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "No text to synthesize"}))
                    continue
                voice = payload.get("voice")
                cfg = float(payload.get("cfg_scale", 1.5))
                cmd = StreamCommand(text=text, voice=voice, cfg_scale=cfg)

                for ev in synthesize_stream_pcm(cmd.text, voice=cmd.voice, cfg_scale=cmd.cfg_scale):
                    if ev.get("type") == "pcm":
                        await websocket.send_bytes(ev["data"])
                    else:
                        await websocket.send_text(json.dumps(ev))
                buf.clear()
                continue

            await websocket.send_text(json.dumps({"type": "error", "detail": f"Unknown action: {action}"}))

    except WebSocketDisconnect:
        return
