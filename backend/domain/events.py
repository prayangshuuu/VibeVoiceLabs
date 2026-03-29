"""Event types and a tiny in-process bus for pipeline hooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from core.logging import get_logger

logger = get_logger("vibevoice.events")

Subscriber = Callable[[Any], None]


@dataclass(frozen=True)
class TTSRequested:
    request_id: str
    text_len: int
    voice: Optional[str]
    engine_hint: str


@dataclass(frozen=True)
class TTSSucceeded:
    request_id: str
    output_path: str
    latency_ms: float
    engine: str


@dataclass(frozen=True)
class TTSFailed:
    request_id: str
    error: str
    engine: str


class EventBus:
    def __init__(self) -> None:
        self._subs: Dict[type, List[Subscriber]] = {}

    def subscribe(self, event_type: type, fn: Subscriber) -> None:
        self._subs.setdefault(event_type, []).append(fn)

    def publish(self, event: Any) -> None:
        for fn in self._subs.get(type(event), []):
            try:
                fn(event)
            except Exception:
                logger.exception("event handler failed for %s", type(event).__name__)


_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
