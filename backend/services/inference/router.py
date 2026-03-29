"""Select engine from request shape (text length) with retries and fallback."""

from __future__ import annotations

import time

from config import Settings
from domain.events import TTSFailed, TTSSucceeded, TTSRequested, get_event_bus
from domain.models import InferenceRequest, InferenceResult
from services.inference.engine import BatchEngine, InferenceEngine, RealtimeEngine
from services.voice.manager import VoiceManager


class InferenceRouter:
    def __init__(self, settings: Settings, voice_manager: VoiceManager) -> None:
        self._settings = settings
        self._realtime = RealtimeEngine(voice_manager, settings.realtime_chunk_chars)
        self._batch = BatchEngine(voice_manager, settings.batch_chunk_chars)

    def pick_engine(self, text: str) -> InferenceEngine:
        if len(text) < self._settings.realtime_text_threshold:
            return self._realtime
        return self._batch

    def _fallback_order(self, primary: InferenceEngine) -> list[InferenceEngine]:
        if primary is self._batch and self._settings.fallback_to_realtime_on_batch_failure:
            return [self._batch, self._realtime]
        return [primary]

    async def generate_with_resilience(
        self,
        request: InferenceRequest,
        *,
        request_id: str,
    ) -> InferenceResult:
        bus = get_event_bus()
        primary = self.pick_engine(request.text)
        bus.publish(
            TTSRequested(
                request_id=request_id,
                text_len=len(request.text),
                voice=request.voice,
                engine_hint=primary.name,
            )
        )
        t0 = time.perf_counter()
        last_exc: Exception | None = None
        retries = self._settings.generation_max_retries

        for engine in self._fallback_order(primary):
            for attempt in range(retries + 1):
                try:
                    result = await engine.generate(request)
                    bus.publish(
                        TTSSucceeded(
                            request_id=request_id,
                            output_path=result.output_path,
                            latency_ms=(time.perf_counter() - t0) * 1000,
                            engine=result.engine,
                        )
                    )
                    return result
                except Exception as e:
                    last_exc = e

        assert last_exc is not None
        bus.publish(
            TTSFailed(
                request_id=request_id,
                error=str(last_exc),
                engine=primary.name,
            )
        )
        raise last_exc

    def generate_with_resilience_sync(
        self,
        request: InferenceRequest,
        *,
        request_id: str,
    ) -> InferenceResult:
        """Same as async variant for worker threads (no event loop)."""
        bus = get_event_bus()
        primary = self.pick_engine(request.text)
        bus.publish(
            TTSRequested(
                request_id=request_id,
                text_len=len(request.text),
                voice=request.voice,
                engine_hint=primary.name,
            )
        )
        t0 = time.perf_counter()
        last_exc: Exception | None = None
        retries = self._settings.generation_max_retries

        for engine in self._fallback_order(primary):
            for attempt in range(retries + 1):
                try:
                    result = engine.generate_sync(request)
                    bus.publish(
                        TTSSucceeded(
                            request_id=request_id,
                            output_path=result.output_path,
                            latency_ms=(time.perf_counter() - t0) * 1000,
                            engine=result.engine,
                        )
                    )
                    return result
                except Exception as e:
                    last_exc = e

        assert last_exc is not None
        bus.publish(
            TTSFailed(
                request_id=request_id,
                error=str(last_exc),
                engine=primary.name,
            )
        )
        raise last_exc
