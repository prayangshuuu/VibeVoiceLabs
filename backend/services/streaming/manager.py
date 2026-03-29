"""WebSocket stream sessions and structured event envelopes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StreamSession:
    session_id: str
    chunks_sent: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)


class StreamingSessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, StreamSession] = {}

    def create_session(self, **meta: Any) -> StreamSession:
        sid = uuid.uuid4().hex
        s = StreamSession(session_id=sid, meta=dict(meta))
        self._sessions[sid] = s
        return s

    def end_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def structured_event(
        self,
        session: StreamSession,
        kind: str,
        *,
        stage: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": kind,
            "session_id": session.session_id,
        }
        if stage:
            payload["stage"] = stage
        if extra:
            payload.update(extra)
        return payload

    def list_active(self) -> List[str]:
        return list(self._sessions.keys())
