"""Async in-process job queue (no Redis)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class TTSJob:
    """Callable payload executed on a worker thread."""

    run: Callable[[], Any]
    label: str = "tts"


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._q: asyncio.Queue[tuple[TTSJob, asyncio.Future[Any]]] = asyncio.Queue()

    @property
    def queue_size(self) -> int:
        return self._q.qsize()

    async def enqueue(self, job: TTSJob) -> Any:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        await self._q.put((job, fut))
        return await fut

    async def worker_loop(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                job, fut = await asyncio.wait_for(self._q.get(), timeout=0.25)
            except asyncio.TimeoutError:
                continue
            try:
                result = await asyncio.to_thread(job.run)
                if not fut.done():
                    fut.set_result(result)
            except Exception as e:
                if not fut.done():
                    fut.set_exception(e)
            finally:
                self._q.task_done()
