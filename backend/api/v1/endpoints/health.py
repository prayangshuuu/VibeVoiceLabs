from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def api_health():
    return {"status": "ok", "service": "vibevoice-tts", "api_version": "v1"}
