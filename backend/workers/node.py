"""Simulated worker node: local queue, load tracking, async job processing."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple

from core.logging import get_logger
from infra.cluster.jobs import Job, JobKind, JobStatus
from services.models.manager import ModelManager
from services.routing.model_router import resolve_asr_model, resolve_tts_model

if TYPE_CHECKING:
    pass

logger = get_logger("vibevoice.worker_node")

TTS_TIMEOUT_S = 600.0
ASR_TIMEOUT_S = 60.0


class WorkerNode:
    def __init__(
        self,
        node_id: int,
        model_manager: ModelManager,
        *,
        on_job_latency_s: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.id = node_id
        self.status = "ready"
        self._local: asyncio.Queue[Tuple[Job, asyncio.Future[Any]]] = asyncio.Queue()
        self._in_flight = 0
        self.draining = False
        self.supported_models = ["tts_realtime", "asr_7b", "asr_mock"]
        self._model_manager = model_manager
        self._on_job_latency_s = on_job_latency_s

    @property
    def local_queue_depth(self) -> int:
        return self._local.qsize()

    @property
    def current_load(self) -> int:
        return self._local.qsize() + self._in_flight

    def begin_drain(self) -> None:
        self.draining = True
        self.status = "draining"

    async def deliver(self, job: Job, fut: asyncio.Future[Any]) -> None:
        await self._local.put((job, fut))

    async def consume_loop(self, stop: asyncio.Event) -> None:
        logger.info("WorkerNode id=%s consumer started", self.id)
        try:
            while not stop.is_set():
                try:
                    job, fut = await asyncio.wait_for(self._local.get(), timeout=0.25)
                except asyncio.TimeoutError:
                    continue
                self._in_flight += 1
                job.status = JobStatus.RUNNING
                t0 = time.perf_counter()
                try:
                    result = await self._process_with_resilience(job)
                    job.status = JobStatus.SUCCEEDED
                    if not fut.done():
                        fut.set_result(result)
                except Exception as e:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    if not fut.done():
                        fut.set_exception(e)
                finally:
                    self._in_flight -= 1
                    elapsed = time.perf_counter() - t0
                    if self._on_job_latency_s:
                        self._on_job_latency_s(elapsed)
                    try:
                        from observability.metrics import get_metrics

                        get_metrics().record_cluster_job(elapsed)
                    except Exception:
                        pass
        except asyncio.CancelledError:
            raise
        finally:
            logger.info("WorkerNode id=%s consumer stopped", self.id)

    async def _process_with_resilience(self, job: Job) -> Any:
        last_exc: Optional[BaseException] = None
        for attempt in range(job.max_attempts):
            job.attempts = attempt + 1
            try:
                if job.kind == JobKind.TTS:
                    job.routed_model = resolve_tts_model()
                    run = job.payload["run_sync"]
                    return await asyncio.wait_for(asyncio.to_thread(run), timeout=TTS_TIMEOUT_S)
                if job.kind == JobKind.ASR:
                    return await asyncio.wait_for(self._run_asr(job), timeout=ASR_TIMEOUT_S)
                raise ValueError(f"Unknown job kind: {job.kind}")
            except BaseException as e:
                last_exc = e
                logger.warning(
                    "WorkerNode id=%s job id=%s attempt %s/%s failed: %s",
                    self.id,
                    job.id,
                    attempt + 1,
                    job.max_attempts,
                    e,
                )
        assert last_exc is not None
        raise last_exc

    async def _run_asr(self, job: Job) -> dict[str, Any]:
        audio_bytes: bytes = job.payload["audio_bytes"]
        filename: str = job.payload["filename"]
        model_id, backend = resolve_asr_model(self._model_manager)
        job.routed_model = model_id

        def _tx() -> str:
            return backend.transcribe(audio_bytes, filename)

        try:
            text = await asyncio.to_thread(_tx)
        except Exception as e:
            if model_id != "asr_mock":
                logger.warning("ASR primary failed (%s), falling back to mock: %s", model_id, e)
                mock = self._model_manager.load_model("asr_mock")
                text = await asyncio.to_thread(lambda: mock.transcribe(audio_bytes, filename))
                job.routed_model = "asr_mock"
            else:
                raise
        return {
            "transcription": text,
            "model": job.routed_model,
            "job_id": job.id,
            "request_id": job.payload.get("request_id", ""),
        }
