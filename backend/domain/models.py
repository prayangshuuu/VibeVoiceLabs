"""Domain types for inference and TTS."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class InferenceRequest:
    text: str
    voice: Optional[str] = None
    cfg_scale: float = 1.5
    multi_speaker: bool = False
    speaker_voice_map: Optional[Dict[str, str]] = None
    output_dir: Optional[Path] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResult:
    output_path: str
    engine: str
    strategy: str
