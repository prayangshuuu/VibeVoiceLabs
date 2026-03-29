"""Registered inference models (metadata + loaders). TTS uses VibeVoice realtime; ASR is lazy / simulated."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Dict, Literal, Optional, TypedDict

logger = logging.getLogger("vibevoice.models.registry")


class ModelEntry(TypedDict, total=False):
    name: str
    type: Literal["tts", "asr"]
    memory_cost_gb: float
    latency_estimate_ms: float
    loader: Callable[[], Any]
    description: str


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.environ.get(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _load_tts_realtime() -> Any:
    """Return already-loaded global TTS weights (eager load at app startup)."""
    from infra.model_loader import get_loaded

    return get_loaded()


def _try_load_asr_7b() -> Optional[Any]:
    """
    Lazy ASR-7B slot: real weights are optional; default is unavailable so routing falls back.
    Set ASR_7B_SIMULATED=1 to load a zero-weight simulated backend for demos.
    """
    if not _env_bool("ASR_7B_SIMULATED", False):
        logger.info("ASR-7B not configured (set ASR_7B_SIMULATED=1 for simulated 7B)")
        return None
    logger.info("Loading simulated ASR-7B backend…")
    time.sleep(0.08)
    return _SimulatedASR7B()


class _SimulatedASR7B:
    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        n = len(audio_bytes)
        return (
            f"[VibeVoice-ASR-7B simulated] transcript for {filename!r} "
            f"({n} bytes; demo backend — no real speech model loaded)"
        )


def _load_asr_mock() -> Any:
    from services.models.backends import MockASRBackend

    return MockASRBackend()


MODELS: Dict[str, ModelEntry] = {
    "tts_realtime": {
        "name": "VibeVoice-Realtime-0.5B",
        "type": "tts",
        "memory_cost_gb": 2.0,
        "latency_estimate_ms": 800.0,
        "loader": _load_tts_realtime,
        "description": "Low-latency streaming TTS (Microsoft VibeVoice realtime)",
    },
    "asr_7b": {
        "name": "VibeVoice-ASR-7B",
        "type": "asr",
        "memory_cost_gb": 7.0,
        "latency_estimate_ms": 1200.0,
        "loader": _try_load_asr_7b,
        "description": "Large ASR (lazy); unavailable unless ASR_7B_SIMULATED=1",
    },
    "asr_mock": {
        "name": "ASR-Mock-Lightweight",
        "type": "asr",
        "memory_cost_gb": 0.01,
        "latency_estimate_ms": 5.0,
        "loader": _load_asr_mock,
        "description": "Deterministic mock transcription for fallback and local dev",
    },
}
