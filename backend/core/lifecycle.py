"""Application lifespan: model load, workers, shutdown."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from config import get_settings
from core.logging import get_logger, setup_logging
from core.rate_limit import RateLimiter
from domain.events import TTSFailed, TTSRequested, TTSSucceeded, get_event_bus
from infra.cache.memory import GenerationCache
from infra.model_loader import load_model
from infra.queue.in_memory import InMemoryJobQueue
from observability.metrics import get_metrics
from core.runtime_ctx import RuntimeContext, clear_runtime_context, set_runtime_context
from services.inference.router import InferenceRouter
from services.streaming.manager import StreamingSessionManager
from services.voice.manager import VoiceManager
from workers.tts_worker import start_tts_workers, stop_tts_workers

logger = get_logger("vibevoice.lifecycle")
_events_wired = False


def _wire_event_logging() -> None:
    global _events_wired
    if _events_wired:
        return
    _events_wired = True
    bus = get_event_bus()

    def on_req(e: TTSRequested) -> None:
        logger.debug("event TTSRequested id=%s len=%s engine=%s", e.request_id, e.text_len, e.engine_hint)

    def on_ok(e: TTSSucceeded) -> None:
        logger.info(
            "event TTSSucceeded id=%s engine=%s latency_ms=%.1f",
            e.request_id,
            e.engine,
            e.latency_ms,
        )

    def on_fail(e: TTSFailed) -> None:
        logger.warning("event TTSFailed id=%s engine=%s err=%s", e.request_id, e.engine, e.error)

    bus.subscribe(TTSRequested, on_req)
    bus.subscribe(TTSSucceeded, on_ok)
    bus.subscribe(TTSFailed, on_fail)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    settings = get_settings()
    logger.info("Loading VibeVoice model…")
    load_model(model_path=settings.vibevoice_model_path, device=settings.vibevoice_device)

    _wire_event_logging()

    app.state.settings = settings
    app.state.metrics = get_metrics()
    app.state.voice_manager = VoiceManager(settings)
    app.state.job_queue = InMemoryJobQueue()
    app.state.inference_router = InferenceRouter(settings, app.state.voice_manager)
    app.state.generation_cache = (
        GenerationCache(settings.cache_max_entries) if settings.caching_enabled else None
    )
    app.state.rate_limiter = RateLimiter(settings.rate_limit_rpm)
    app.state.streaming_manager = StreamingSessionManager()
    set_runtime_context(
        RuntimeContext(
            settings=settings,
            voice_manager=app.state.voice_manager,
            streaming_manager=app.state.streaming_manager,
        )
    )

    stop_event = asyncio.Event()
    app.state.tts_stop_event = stop_event
    app.state.tts_worker_tasks = await start_tts_workers(
        app.state.job_queue,
        stop_event,
        concurrency=settings.worker_concurrency,
    )
    logger.info("TTS workers started (concurrency=%s)", settings.worker_concurrency)

    yield

    stop_event.set()
    await stop_tts_workers(app.state.tts_worker_tasks)
    clear_runtime_context()
    logger.info("Shutdown complete")
