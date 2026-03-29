"""Central configuration (env + defaults)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    if v is None or not v.strip():
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    if v is None or not v.strip():
        return default
    try:
        return float(v)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Application settings — tune without code changes."""

    # Model
    vibevoice_model_path: str = field(
        default_factory=lambda: os.environ.get("VIBEVOICE_MODEL_PATH", "microsoft/VibeVoice-Realtime-0.5B")
    )
    vibevoice_device: str | None = field(default_factory=lambda: os.environ.get("VIBEVOICE_DEVICE") or None)
    vibevoice_voices_dir: str | None = field(default_factory=lambda: os.environ.get("VIBEVOICE_VOICES_DIR") or None)

    # Inference routing
    realtime_text_threshold: int = field(default_factory=lambda: _env_int("REALTIME_TEXT_THRESHOLD", 200))
    realtime_chunk_chars: int = field(default_factory=lambda: _env_int("REALTIME_CHUNK_CHARS", 220))
    batch_chunk_chars: int = field(default_factory=lambda: _env_int("BATCH_CHUNK_CHARS", 420))

    # Features
    caching_enabled: bool = field(default_factory=lambda: _env_bool("TTS_CACHE_ENABLED", True))
    cache_max_entries: int = field(default_factory=lambda: _env_int("TTS_CACHE_MAX_ENTRIES", 128))
    streaming_enabled: bool = field(default_factory=lambda: _env_bool("STREAMING_ENABLED", True))

    # Worker queue / distributed cluster (simulated locally, no Redis)
    worker_concurrency: int = field(default_factory=lambda: max(1, _env_int("TTS_WORKER_CONCURRENCY", 2)))
    tts_via_worker_queue: bool = field(default_factory=lambda: _env_bool("TTS_VIA_WORKER_QUEUE", True))
    cluster_enabled: bool = field(default_factory=lambda: _env_bool("CLUSTER_ENABLED", True))
    cluster_initial_workers: int = field(default_factory=lambda: max(1, _env_int("CLUSTER_INITIAL_WORKERS", 3)))
    cluster_min_workers: int = field(default_factory=lambda: max(1, _env_int("CLUSTER_MIN_WORKERS", 1)))
    cluster_max_workers: int = field(default_factory=lambda: max(1, _env_int("CLUSTER_MAX_WORKERS", 8)))
    autoscaler_queue_scale_up_threshold: int = field(
        default_factory=lambda: max(1, _env_int("AUTOSCALER_QUEUE_THRESHOLD", 10))
    )
    autoscaler_tick_s: float = field(default_factory=lambda: max(0.25, _env_float("AUTOSCALER_TICK_S", 2.0)))
    model_memory_budget_gb: float = field(default_factory=lambda: max(1.0, _env_float("MODEL_MEMORY_BUDGET_GB", 24.0)))

    # Resilience
    generation_max_retries: int = field(default_factory=lambda: max(0, _env_int("GENERATION_MAX_RETRIES", 2)))
    fallback_to_realtime_on_batch_failure: bool = field(
        default_factory=lambda: _env_bool("FALLBACK_TO_REALTIME_ON_BATCH_FAILURE", True)
    )

    # Rate limits (in-memory)
    rate_limit_rpm: int = field(default_factory=lambda: _env_int("RATE_LIMIT_RPM", 120))
    max_chars_per_request: int = field(default_factory=lambda: _env_int("MAX_CHARS_PER_REQUEST", 8000))

    # API
    api_key: str = field(default_factory=lambda: os.environ.get("API_KEY", "").strip())

    # Paths (resolved at runtime relative to backend root)
    storage_outputs_subdir: str = "storage/outputs"

    # Observability
    metrics_enabled: bool = field(default_factory=lambda: _env_bool("METRICS_ENABLED", True))
    tracing_enabled: bool = field(default_factory=lambda: _env_bool("TRACING_ENABLED", True))


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Convenient alias for imports
settings = get_settings()
