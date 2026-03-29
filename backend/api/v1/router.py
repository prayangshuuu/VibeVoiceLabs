"""Aggregate /api/v1 routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.v1.endpoints import asr, cluster, health, metrics, stream, tts, voices

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(metrics.router, tags=["metrics"])
api_v1_router.include_router(cluster.router, tags=["cluster"])
api_v1_router.include_router(voices.router, tags=["voices"])
api_v1_router.include_router(tts.router, tags=["tts"])
api_v1_router.include_router(asr.router, tags=["asr"])
api_v1_router.include_router(stream.router, tags=["stream"])
