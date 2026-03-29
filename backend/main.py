"""VibeVoiceLabs — production-style FastAPI entrypoint."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.legacy import legacy_router
from api.v1.router import api_v1_router
from core.lifecycle import lifespan
from core.metrics_middleware import MetricsMiddleware
from core.middleware import RequestContextMiddleware
from core.rate_limit_middleware import RateLimitMiddleware
from middleware.api_key import APIKeyMiddleware

# Uvicorn often binds 0.0.0.0; Swagger/OpenAPI would otherwise advertise that host,
# which browsers cannot use. Force a public base URL (override in Docker/prod via env).
_PUBLIC_API_BASE = os.environ.get("PUBLIC_API_BASE_URL", "http://localhost:8000").rstrip("/")

app = FastAPI(
    title="VibeVoice TTS Platform",
    description="Modular, observable TTS API (VibeVoice-Realtime-0.5B).",
    version="1.0.0",
    lifespan=lifespan,
    servers=[{"url": _PUBLIC_API_BASE, "description": "Public API base (Swagger / clients)"}],
)

# Starlette: last add_middleware = outermost on the request path.
# Order inbound: request id → metrics → rate limit → API key → CORS → routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(legacy_router)

_outputs = Path(__file__).resolve().parent / "storage" / "outputs"
_outputs.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(_outputs)), name="audio")


@app.get("/health")
def health_root():
    return {"status": "ok", "service": "vibevoice-tts"}


@app.get("/")
def root():
    return {
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
        "legacy": {
            "tts": "POST /tts",
            "voices": "GET /voices",
            "websocket": "WS /stream",
        },
    }
