"""Simulated horizontal scaling decisions based on queue depth and idle workers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutoscaleDecision:
    scale_up: int = 0
    scale_down: int = 0
    reason: str = ""


class Autoscaler:
    def __init__(
        self,
        *,
        queue_scale_up_threshold: int = 10,
        min_workers: int = 1,
        max_workers: int = 8,
    ) -> None:
        self.queue_scale_up_threshold = queue_scale_up_threshold
        self.min_workers = min_workers
        self.max_workers = max_workers

    def evaluate(
        self,
        *,
        queue_depth: int,
        worker_count: int,
        idle_worker_count: int,
    ) -> AutoscaleDecision:
        if queue_depth > self.queue_scale_up_threshold and worker_count < self.max_workers:
            return AutoscaleDecision(scale_up=1, reason="queue_hot")
        if idle_worker_count > 1 and worker_count > self.min_workers and queue_depth == 0:
            return AutoscaleDecision(scale_down=1, reason="idle_surplus")
        return AutoscaleDecision()
