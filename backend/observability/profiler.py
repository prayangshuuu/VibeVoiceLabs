"""Fine-grained timing for inference chunks (dev-friendly)."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Callable, Generator, TypeVar

from observability.metrics import get_metrics

T = TypeVar("T")


@contextmanager
def profile_chunk(label: str) -> Generator[None, None, None]:
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt_ms = (time.perf_counter() - t0) * 1000
        get_metrics().record_generation(dt_ms)


def profiled(label: str, fn: Callable[[], T]) -> T:
    with profile_chunk(label):
        return fn()
