"""Non-streaming TTS and voice listing."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.inference import synthesize_to_file
from services.voices import list_voices

router = APIRouter(tags=["tts"])


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
        description="Optional map of speaker label -> voice id, e.g. {'A': 'carter', 'B': 'emma'}",
    )


class TTSResponse(BaseModel):
    filename: str
    output_path: str
    audio_url: str
    message: str = "ok"


@router.get("/voices")
def get_voices():
    """List predefined voices and whether voice .pt files are present locally."""
    return {"voices": list_voices()}


@router.post("/tts", response_model=TTSResponse)
def post_tts(req: TTSRequest, request: Request):
    try:
        out = synthesize_to_file(
            text=req.text,
            voice=req.voice,
            cfg_scale=req.cfg_scale,
            multi_speaker=req.multi_speaker,
            speaker_voice_map=req.speaker_voices,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}") from e

    p = Path(out)
    filename = p.name
    base = str(request.base_url).rstrip("/")
    return TTSResponse(
        filename=filename,
        output_path=out,
        audio_url=f"{base}/audio/{filename}",
    )
