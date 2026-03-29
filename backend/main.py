"""VibeVoice-Realtime-0.5B FastAPI backend (local-first ElevenLabs-style TTS)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from middleware.api_key import APIKeyMiddleware
from routes import stream, tts
from services.model_loader import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(
    title="VibeVoice TTS API",
    description="Text-to-speech using Microsoft VibeVoice-Realtime-0.5B (streaming + REST).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(APIKeyMiddleware)

app.include_router(tts.router)
app.include_router(stream.router)

_outputs = Path(__file__).resolve().parent / "storage" / "outputs"
_outputs.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(_outputs)), name="audio")


@app.get("/health")
def health():
    return {"status": "ok", "service": "vibevoice-tts"}


@app.get("/")
def root():
    return {
        "docs": "/docs",
        "health": "/health",
        "tts": "POST /tts",
        "voices": "GET /voices",
        "websocket": "WS /stream",
    }
