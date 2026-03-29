"""Simple in-memory fixed-window rate limiting per client IP."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict


class RateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = max(1, requests_per_minute)
        self._by_client: Dict[str, Deque[float]] = defaultdict(lambda: deque())

    def allow(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        q = self._by_client[client_id]
        while q and q[0] < window_start:
            q.popleft()
        if len(q) >= self.requests_per_minute:
            return False
        q.append(now)
        return True
