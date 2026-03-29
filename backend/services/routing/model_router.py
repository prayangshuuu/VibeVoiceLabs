"""Map job kinds to concrete model ids with fallback."""

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

from infra.cluster.jobs import JobKind

if TYPE_CHECKING:
    from services.models.manager import ModelManager


def resolve_tts_model() -> str:
    return "tts_realtime"


def resolve_asr_model(manager: ModelManager) -> Tuple[str, object]:
    """
    Prefer ASR-7B when load_if_available succeeds; else mock.
    Returns (model_id, backend).
    """
    backend = manager.load_if_available("asr_7b")
    if backend is not None:
        return "asr_7b", backend
    mock = manager.load_model("asr_mock")
    return "asr_mock", mock
