"""Lightweight request tracing (no external collector required)."""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

from config import get_settings

_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_spans: ContextVar[List["Span"]] = ContextVar("spans", default=[])


@dataclass
class Span:
    name: str
    start_ns: int
    end_ns: Optional[int] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.end_ns is None:
            return 0.0
        return (self.end_ns - self.start_ns) / 1_000_000


def new_trace_id() -> str:
    return uuid.uuid4().hex


def set_trace_id(tid: Optional[str]) -> None:
    _trace_id.set(tid)


def get_trace_id() -> Optional[str]:
    return _trace_id.get()


@contextmanager
def span(name: str, **meta: Any) -> Generator[Span, None, None]:
    if not get_settings().tracing_enabled:
        now = time.perf_counter_ns()
        yield Span(name=name, start_ns=now, end_ns=now, meta=dict(meta))
        return
    sp = Span(name=name, start_ns=time.perf_counter_ns(), meta=dict(meta))
    stack = list(_spans.get() or [])
    stack.append(sp)
    _spans.set(stack)
    try:
        yield sp
    finally:
        sp.end_ns = time.perf_counter_ns()
        cur = list(_spans.get() or [])
        if cur and cur[-1] is sp:
            cur.pop()
            _spans.set(cur)


def current_spans_snapshot() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in _spans.get() or []:
        out.append(
            {
                "name": s.name,
                "duration_ms": round(s.duration_ms, 3),
                "meta": s.meta,
            }
        )
    return out


def reset_trace_context() -> None:
    _trace_id.set(None)
    _spans.set([])
