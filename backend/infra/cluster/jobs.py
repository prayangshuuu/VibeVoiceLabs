"""Typed inference jobs for the distributed queue (in-process, no Redis)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class JobKind(str, Enum):
    TTS = "tts"
    ASR = "asr"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    """Unit of work routed to a worker node."""

    id: str
    kind: JobKind
    payload: dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    routed_model: str = ""
    attempts: int = 0
    max_attempts: int = 3
    error: Optional[str] = None

    @staticmethod
    def new_tts(
        *,
        run_sync: Callable[[], Any],
        request_id: str,
        max_attempts: int = 3,
    ) -> Job:
        return Job(
            id=str(uuid.uuid4()),
            kind=JobKind.TTS,
            payload={"run_sync": run_sync, "request_id": request_id},
            max_attempts=max_attempts,
        )

    @staticmethod
    def new_asr(
        *,
        audio_bytes: bytes,
        filename: str,
        request_id: str,
        max_attempts: int = 3,
    ) -> Job:
        return Job(
            id=str(uuid.uuid4()),
            kind=JobKind.ASR,
            payload={
                "audio_bytes": audio_bytes,
                "filename": filename,
                "request_id": request_id,
            },
            max_attempts=max_attempts,
        )
