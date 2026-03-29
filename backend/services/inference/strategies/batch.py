"""Batch-oriented chunking (fewer, larger segments — future batch workers)."""

from __future__ import annotations

from domain.models import InferenceRequest, InferenceResult
from services.inference.generation import synthesize_to_file_sync
from services.voice.manager import VoiceManager


class BatchStrategy:
    name = "batch"

    def __init__(self, voice_manager: VoiceManager, chunk_max_chars: int) -> None:
        self._voice_manager = voice_manager
        self._chunk_max_chars = chunk_max_chars

    def synthesize(self, req: InferenceRequest, *, engine_name: str) -> InferenceResult:
        path = synthesize_to_file_sync(
            req,
            voice_manager=self._voice_manager,
            chunk_max_chars=self._chunk_max_chars,
        )
        return InferenceResult(output_path=path, engine=engine_name, strategy=self.name)
