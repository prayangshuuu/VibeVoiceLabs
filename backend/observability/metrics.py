"""In-process metrics for /api/v1/metrics."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


@dataclass
class MetricsRegistry:
    requests_total: int = 0
    errors_total: int = 0
    generations_total: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _latencies_ms: Deque[float] = field(default_factory=lambda: deque(maxlen=500))
    _gen_times_ms: Deque[float] = field(default_factory=lambda: deque(maxlen=500))
    _started: float = field(default_factory=time.perf_counter)

    def record_request(self, latency_ms: float, *, error: bool) -> None:
        with self._lock:
            self.requests_total += 1
            if error:
                self.errors_total += 1
            self._latencies_ms.append(latency_ms)

    def record_generation(self, duration_ms: float) -> None:
        with self._lock:
            self.generations_total += 1
            self._gen_times_ms.append(duration_ms)

    def snapshot(self, queue_size: int = 0) -> Dict[str, object]:
        with self._lock:
            uptime = time.perf_counter() - self._started
            rps = self.requests_total / uptime if uptime > 0 else 0.0
            lat_avg = sum(self._latencies_ms) / len(self._latencies_ms) if self._latencies_ms else 0.0
            gen_avg = sum(self._gen_times_ms) / len(self._gen_times_ms) if self._gen_times_ms else 0.0
            return {
                "uptime_seconds": round(uptime, 3),
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "generations_total": self.generations_total,
                "requests_per_sec": round(rps, 4),
                "avg_request_latency_ms": round(lat_avg, 3),
                "avg_generation_time_ms": round(gen_avg, 3),
                "queue_size": queue_size,
            }


_registry: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    global _registry
    if _registry is None:
        _registry = MetricsRegistry()
    return _registry
