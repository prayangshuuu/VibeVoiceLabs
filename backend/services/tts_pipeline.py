"""Orchestrates cache, queue, and inference router for HTTP TTS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from config import Settings
from domain.models import InferenceRequest, InferenceResult
from infra.cache.memory import GenerationCache, tts_cache_key
from infra.queue.in_memory import InMemoryJobQueue, TTSJob
from services.inference.router import InferenceRouter
from services.voice.manager import VoiceManager


def _outputs_dir(settings: Settings) -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / settings.storage_outputs_subdir


async def run_tts(
    *,
    settings: Settings,
    voice_manager: VoiceManager,
    inference_router: InferenceRouter,
    job_queue: InMemoryJobQueue,
    generation_cache: Optional[GenerationCache],
    text: str,
    voice: Optional[str],
    cfg_scale: float,
    multi_speaker: bool,
    speaker_voice_map: Optional[dict],
    request_id: str,
) -> InferenceResult:
    cache_key = tts_cache_key(text, voice, multi_speaker, cfg_scale, speaker_voice_map)
    if generation_cache is not None:
        hit = generation_cache.get_path(cache_key)
        if hit:
            return InferenceResult(output_path=hit, engine="cache", strategy="cache")

    req = InferenceRequest(
        text=text,
        voice=voice,
        cfg_scale=cfg_scale,
        multi_speaker=multi_speaker,
        speaker_voice_map=speaker_voice_map,
        output_dir=_outputs_dir(settings),
    )

    if settings.tts_via_worker_queue:

        def run() -> InferenceResult:
            return inference_router.generate_with_resilience_sync(req, request_id=request_id)

        result = await job_queue.enqueue(TTSJob(run=run, label="tts"))
    else:
        result = await inference_router.generate_with_resilience(req, request_id=request_id)

    if generation_cache is not None:
        generation_cache.put_path(cache_key, result.output_path)
    return result
