from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.runtime_ctx import get_runtime_context
from core.security import validate_api_key_ws
from core.tracing import span
from services.inference.generation import synthesize_stream_pcm

router = APIRouter()


class StreamCommand(BaseModel):
    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    cfg_scale: float = Field(1.5, ge=0.5, le=3.0)
    multi_speaker: bool = False
    speaker_voices: Optional[Dict[str, str]] = None


@router.websocket("/stream")
async def stream_ws_v1(websocket: WebSocket):
    await websocket.accept()
    if not validate_api_key_ws(dict(websocket.headers), dict(websocket.query_params)):
        await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid API key"}))
        await websocket.close(code=4401)
        return

    ctx = get_runtime_context()
    settings = ctx.settings
    if not settings.streaming_enabled:
        await websocket.send_text(json.dumps({"type": "error", "detail": "Streaming disabled by configuration"}))
        await websocket.close(code=4403)
        return

    vm = ctx.voice_manager
    sm = ctx.streaming_manager
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
                await websocket.send_text(
                    json.dumps({"type": "progress", "stage": "reset", "message": "Buffer cleared"})
                )
                continue

            if action == "append_text":
                t = (payload.get("text") or "").strip()
                if t:
                    buf.append(t)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "progress",
                            "stage": "buffer",
                            "chars": sum(len(x) for x in buf),
                            "demo": True,
                        }
                    )
                )
                continue

            if action == "synthesize":
                text = (payload.get("text") or "").strip()
                if not text and buf:
                    text = "\n".join(buf)
                if not text:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "No text to synthesize"}))
                    continue
                if len(text) > settings.max_chars_per_request:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "detail": f"Text exceeds max length ({settings.max_chars_per_request} characters).",
                            }
                        )
                    )
                    continue

                voice = payload.get("voice")
                cfg = float(payload.get("cfg_scale", 1.5))
                multi = bool(payload.get("multi_speaker", False))
                sv = payload.get("speaker_voices")
                if multi and isinstance(sv, dict):
                    speaker_map = {str(k): str(v) for k, v in sv.items()}
                else:
                    speaker_map = None

                try:
                    cmd = StreamCommand(
                        text=text, voice=voice, cfg_scale=cfg, multi_speaker=multi, speaker_voices=speaker_map
                    )
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "detail": str(e)}))
                    continue

                session = sm.create_session(voice=cmd.voice)
                await websocket.send_text(
                    json.dumps(sm.structured_event(session, "session", stage="ready", extra={"voice": cmd.voice}))
                )

                chunk_chars = settings.realtime_chunk_chars
                with span("stream.synthesize", session_id=session.session_id):
                    try:
                        for ev in synthesize_stream_pcm(
                            cmd.text,
                            vm,
                            cmd.voice,
                            cmd.cfg_scale,
                            chunk_chars,
                            multi_speaker=cmd.multi_speaker,
                            speaker_voice_map=cmd.speaker_voices,
                        ):
                            if ev.get("type") == "pcm":
                                session.chunks_sent += 1
                                await websocket.send_bytes(ev["data"])
                            else:
                                enriched = {**ev, "session_id": session.session_id}
                                await websocket.send_text(json.dumps(enriched))
                    except Exception as e:
                        await websocket.send_text(
                            json.dumps(
                                sm.structured_event(
                                    session,
                                    "error",
                                    stage="failed",
                                    extra={"detail": str(e)},
                                )
                            )
                        )
                    finally:
                        sm.end_session(session.session_id)

                buf.clear()
                continue

            await websocket.send_text(json.dumps({"type": "error", "detail": f"Unknown action: {action}"}))

    except WebSocketDisconnect:
        return
