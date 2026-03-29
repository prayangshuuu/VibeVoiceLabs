"""Voice catalog, path resolution, and embedding cache."""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import torch

from config import Settings
from infra.cache.memory import VoiceEmbeddingCache


@dataclass(frozen=True)
class VoiceInfo:
    id: str
    label: str
    filename: str


DEFAULT_VOICE_PRESETS: List[VoiceInfo] = [
    VoiceInfo("carter", "Carter (English, male)", "en-Carter_man.pt"),
    VoiceInfo("davis", "Davis (English, male)", "en-Davis_man.pt"),
    VoiceInfo("emma", "Emma (English, female)", "en-Emma_woman.pt"),
    VoiceInfo("frank", "Frank (English, male)", "en-Frank_man.pt"),
    VoiceInfo("grace", "Grace (English, female)", "en-Grace_woman.pt"),
    VoiceInfo("mike", "Mike (English, male)", "en-Mike_man.pt"),
]


class VoiceManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedding_cache = VoiceEmbeddingCache(max_entries=max(32, settings.cache_max_entries))

    def _voices_dir(self) -> str:
        base = self._settings.vibevoice_voices_dir
        if base:
            return os.path.abspath(base)
        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "voices", "streaming_model")
        )
        return root

    def scan_voice_files(self) -> Dict[str, str]:
        d = self._voices_dir()
        out: Dict[str, str] = {}
        if not os.path.isdir(d):
            return out
        for pt in glob.glob(os.path.join(d, "**", "*.pt"), recursive=True):
            stem = os.path.splitext(os.path.basename(pt))[0].lower()
            out[stem] = os.path.abspath(pt)
        return dict(sorted(out.items()))

    def resolve_voice_path(self, speaker_name: Optional[str]) -> str:
        available = self.scan_voice_files()
        if not available:
            raise FileNotFoundError(
                f"No voice .pt files under {self._voices_dir()}. Run: python scripts/download_voices.py"
            )

        if not speaker_name:
            speaker_name = DEFAULT_VOICE_PRESETS[0].id

        key = speaker_name.strip().lower()

        if key in available:
            return available[key]

        for preset in DEFAULT_VOICE_PRESETS:
            if preset.id == key:
                stem = os.path.splitext(preset.filename)[0].lower()
                if stem in available:
                    return available[stem]
                path = os.path.join(self._voices_dir(), preset.filename)
                if os.path.isfile(path):
                    return os.path.abspath(path)

        matches = [p for stem, p in available.items() if key in stem or stem in key]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous voice '{speaker_name}'; use a preset id: {[p.id for p in DEFAULT_VOICE_PRESETS]}"
            )

        return next(iter(available.values()))

    def get_prefilled(self, voice_id: Optional[str], device: str) -> Any:
        path = self.resolve_voice_path(voice_id)
        target = device if device != "cpu" else "cpu"

        def load() -> Any:
            return torch.load(path, map_location=target, weights_only=False)

        return self._embedding_cache.get_or_load(path, load)

    def list_voices(self) -> List[Dict[str, str]]:
        scanned = self.scan_voice_files()
        rows: List[Dict[str, str]] = []
        seen = set()
        for preset in DEFAULT_VOICE_PRESETS:
            stem = os.path.splitext(preset.filename)[0].lower()
            path = scanned.get(stem)
            rows.append(
                {
                    "id": preset.id,
                    "label": preset.label,
                    "available": str(bool(path)),
                    "filename": preset.filename,
                }
            )
            seen.add(stem)
        for stem, path in scanned.items():
            if stem in seen:
                continue
            rows.append(
                {
                    "id": stem,
                    "label": stem.replace("-", " ").title(),
                    "available": "True",
                    "filename": os.path.basename(path),
                }
            )
        return rows
