"""Cluster supervisor: ingress queue, load-balanced dispatch, simulated autoscaling."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

from config import Settings
from core.logging import get_logger
from infra.cluster.jobs import Job
from scheduler.autoscaler import Autoscaler
from scheduler.load_balancer import pick_least_loaded
from services.models.manager import ModelManager
from workers.node import WorkerNode

logger = get_logger("vibevoice.supervisor")
_autoscaler_log = logging.getLogger("vibevoice.autoscaler")


class ClusterSupervisor:
    def __init__(self, settings: Settings, model_manager: ModelManager) -> None:
        self._settings = settings
        self._model_manager = model_manager
        self._stop = asyncio.Event()
        self._ingress: asyncio.Queue[tuple[Job, asyncio.Future[Any]]] = asyncio.Queue()
        self._nodes: List[WorkerNode] = []
        self._node_tasks: Dict[int, asyncio.Task[None]] = {}
        self._autoscaler = Autoscaler(
            queue_scale_up_threshold=settings.autoscaler_queue_scale_up_threshold,
            min_workers=settings.cluster_min_workers,
            max_workers=settings.cluster_max_workers,
        )
        self._lock = asyncio.Lock()
        self._next_id = 1
        self._dispatcher_task: Optional[asyncio.Task[None]] = None
        self._autoscaler_task: Optional[asyncio.Task[None]] = None
        self._latencies_s: deque[float] = deque(maxlen=500)
        self._completion_times: deque[float] = deque(maxlen=500)
        self._stat_lock = threading.Lock()

    @property
    def worker_count(self) -> int:
        return len(self._nodes)

    @property
    def queue_depth(self) -> int:
        depth = self._ingress.qsize()
        for n in self._nodes:
            depth += n.local_queue_depth
        return depth

    def status_snapshot(self) -> Dict[str, Any]:
        now = time.perf_counter()
        window = 10.0
        with self._stat_lock:
            avg_lat = sum(self._latencies_s) / len(self._latencies_s) if self._latencies_s else 0.0
            recent = sum(1 for t in self._completion_times if now - t <= window)
        jps = recent / window if window > 0 else 0.0
        return {
            "workers": self.worker_count,
            "queue": self.queue_depth,
            "avg_latency": round(avg_lat, 3),
            "jobs_per_sec": round(jps, 4),
            "ingress_depth": self._ingress.qsize(),
        }

    def record_job_latency(self, duration_s: float) -> None:
        with self._stat_lock:
            self._latencies_s.append(duration_s)
            self._completion_times.append(time.perf_counter())

    async def enqueue_job(self, job: Job) -> Any:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        await self._ingress.put((job, fut))
        return await fut

    async def start(self) -> None:
        n0 = max(1, self._settings.cluster_initial_workers)
        async with self._lock:
            for _ in range(n0):
                await self._spawn_node_unlocked()
        self._dispatcher_task = asyncio.create_task(self._dispatcher_loop(), name="cluster-dispatcher")
        self._autoscaler_task = asyncio.create_task(self._autoscaler_loop(), name="cluster-autoscaler")
        logger.info("ClusterSupervisor started (%s worker nodes)", len(self._nodes))

    async def shutdown(self) -> None:
        self._stop.set()
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
        if self._autoscaler_task:
            self._autoscaler_task.cancel()
        for t in list(self._node_tasks.values()):
            t.cancel()
        tasks = [t for t in [self._dispatcher_task, self._autoscaler_task] if t]
        tasks.extend(self._node_tasks.values())
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._node_tasks.clear()
        self._nodes.clear()
        logger.info("ClusterSupervisor shutdown complete")

    async def _spawn_node_unlocked(self) -> WorkerNode:
        nid = self._next_id
        self._next_id += 1
        node = WorkerNode(nid, self._model_manager, on_job_latency_s=self.record_job_latency)
        self._nodes.append(node)
        t = asyncio.create_task(node.consume_loop(self._stop), name=f"node-{nid}-consumer")
        self._node_tasks[nid] = t
        logger.info("[Cluster] Spawned worker node id=%s", nid)
        return node

    async def _dispatcher_loop(self) -> None:
        while not self._stop.is_set():
            try:
                job, fut = await asyncio.wait_for(self._ingress.get(), timeout=0.35)
            except asyncio.TimeoutError:
                continue
            try:
                while not self._stop.is_set():
                    async with self._lock:
                        candidates = [n for n in self._nodes if not n.draining]
                    if candidates:
                        node = pick_least_loaded(candidates, load_key=lambda n: n.current_load)
                        await node.deliver(job, fut)
                        break
                    await asyncio.sleep(0.05)
            except Exception as e:
                if not fut.done():
                    fut.set_exception(e)

    async def _autoscaler_loop(self) -> None:
        tick = max(0.5, self._settings.autoscaler_tick_s)
        while not self._stop.is_set():
            await asyncio.sleep(tick)
            try:
                async with self._lock:
                    depth = self.queue_depth
                    workers = len(self._nodes)
                    idle = sum(1 for n in self._nodes if n.current_load == 0)
                decision = self._autoscaler.evaluate(
                    queue_depth=depth,
                    worker_count=workers,
                    idle_worker_count=idle,
                )
                if decision.scale_up:
                    _autoscaler_log.info("[Autoscaler] Scaling up: +1 worker")
                    async with self._lock:
                        if len(self._nodes) < self._settings.cluster_max_workers:
                            await self._spawn_node_unlocked()
                if decision.scale_down:
                    _autoscaler_log.info("[Autoscaler] Scaling down: -1 worker")
                    await self._retire_one_idle_node()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("autoscaler tick failed")

    async def _retire_one_idle_node(self) -> None:
        async with self._lock:
            if len(self._nodes) <= self._settings.cluster_min_workers:
                return
            victim: Optional[WorkerNode] = None
            for node in reversed(self._nodes):
                if node.current_load == 0:
                    victim = node
                    break
            if victim is None:
                return
            self._nodes = [n for n in self._nodes if n.id != victim.id]
            task = self._node_tasks.pop(victim.id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("[Cluster] Retired worker node id=%s", victim.id)
