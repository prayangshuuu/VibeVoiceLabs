"""ASR request path: cluster queue or inline (when cluster disabled)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from infra.cluster.jobs import Job
from services.routing.model_router import resolve_asr_model

if TYPE_CHECKING:
    from services.models.manager import ModelManager
    from workers.supervisor import ClusterSupervisor


async def run_asr(
    *,
    model_manager: ModelManager,
    cluster_supervisor: Optional[ClusterSupervisor],
    audio_bytes: bytes,
    filename: str,
    request_id: str,
) -> dict[str, Any]:
    if cluster_supervisor is not None:
        job = Job.new_asr(
            audio_bytes=audio_bytes,
            filename=filename,
            request_id=request_id,
        )
        return await cluster_supervisor.enqueue_job(job)
    model_id, backend = resolve_asr_model(model_manager)

    def _tx() -> str:
        return backend.transcribe(audio_bytes, filename)

    try:
        text = await asyncio.to_thread(_tx)
    except Exception:
        mock = model_manager.load_model("asr_mock")
        text = await asyncio.to_thread(lambda: mock.transcribe(audio_bytes, filename))
        model_id = "asr_mock"
    return {
        "transcription": text,
        "model": model_id,
        "job_id": None,
        "request_id": request_id,
    }
