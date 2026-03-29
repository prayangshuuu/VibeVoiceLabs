"""Async worker tasks draining the in-memory TTS queue."""

from __future__ import annotations

import asyncio
from typing import List

from core.logging import get_logger
from infra.queue.in_memory import InMemoryJobQueue

logger = get_logger("vibevoice.worker")


async def start_tts_workers(
    queue: InMemoryJobQueue,
    stop: asyncio.Event,
    *,
    concurrency: int,
) -> List[asyncio.Task[None]]:
    tasks: List[asyncio.Task[None]] = []
    for i in range(concurrency):
        t = asyncio.create_task(_run_worker(f"w{i}", queue, stop), name=f"tts-worker-{i}")
        tasks.append(t)
    return tasks


async def _run_worker(name: str, queue: InMemoryJobQueue, stop: asyncio.Event) -> None:
    logger.info("worker %s started", name)
    try:
        await queue.worker_loop(stop)
    except asyncio.CancelledError:
        raise
    finally:
        logger.info("worker %s stopped", name)


async def stop_tts_workers(tasks: List[asyncio.Task[None]]) -> None:
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
