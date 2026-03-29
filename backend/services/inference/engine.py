"""Pluggable inference engines built on strategies."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from domain.models import InferenceRequest, InferenceResult
from services.inference.strategies.batch import BatchStrategy
from services.inference.strategies.realtime import RealtimeStrategy
from services.voice.manager import VoiceManager


class InferenceEngine(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, request: InferenceRequest) -> InferenceResult:
        ...

    @abstractmethod
    def generate_sync(self, request: InferenceRequest) -> InferenceResult:
        """Run inference on the calling thread (worker pool)."""
        ...


class RealtimeEngine(InferenceEngine):
    name = "realtime"

    def __init__(self, voice_manager: VoiceManager, chunk_max_chars: int) -> None:
        self._strategy = RealtimeStrategy(voice_manager, chunk_max_chars)

    def generate_sync(self, request: InferenceRequest) -> InferenceResult:
        return self._strategy.synthesize(request, engine_name=self.name)

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        return await asyncio.to_thread(self.generate_sync, request)


class BatchEngine(InferenceEngine):
    name = "batch"

    def __init__(self, voice_manager: VoiceManager, chunk_max_chars: int) -> None:
        self._strategy = BatchStrategy(voice_manager, chunk_max_chars)

    def generate_sync(self, request: InferenceRequest) -> InferenceResult:
        return self._strategy.synthesize(request, engine_name=self.name)

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        return await asyncio.to_thread(self.generate_sync, request)
