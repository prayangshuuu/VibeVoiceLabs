"""Process-wide handles for WebSocket handlers (no Request.app on WebSocket)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from config import Settings
    from services.streaming.manager import StreamingSessionManager
    from services.voice.manager import VoiceManager


@dataclass
class RuntimeContext:
    settings: "Settings"
    voice_manager: "VoiceManager"
    streaming_manager: "StreamingSessionManager"


_ctx: Optional[RuntimeContext] = None


def set_runtime_context(ctx: RuntimeContext) -> None:
    global _ctx
    _ctx = ctx


def get_runtime_context() -> RuntimeContext:
    if _ctx is None:
        raise RuntimeError("Runtime context not initialized (lifespan not run?)")
    return _ctx


def clear_runtime_context() -> None:
    global _ctx
    _ctx = None
