"""Predefined voice metadata and resolution of speaker name -> .pt path."""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class VoiceInfo:
    id: str
    label: str
    filename: str


# Curated list (files live under voices/streaming_model/; download via scripts/download_voices.py)
DEFAULT_VOICE_PRESETS: List[VoiceInfo] = [
    VoiceInfo("carter", "Carter (English, male)", "en-Carter_man.pt"),
    VoiceInfo("davis", "Davis (English, male)", "en-Davis_man.pt"),
    VoiceInfo("emma", "Emma (English, female)", "en-Emma_woman.pt"),
    VoiceInfo("frank", "Frank (English, male)", "en-Frank_man.pt"),
    VoiceInfo("grace", "Grace (English, female)", "en-Grace_woman.pt"),
    VoiceInfo("mike", "Mike (English, male)", "en-Mike_man.pt"),
]


def _voices_dir() -> str:
    base = os.environ.get("VIBEVOICE_VOICES_DIR")
    if base:
        return os.path.abspath(base)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "voices", "streaming_model"))
    return root


def scan_voice_files() -> Dict[str, str]:
    """Map lowercase stem -> absolute path for all *.pt under the voices directory."""
    d = _voices_dir()
    out: Dict[str, str] = {}
    if not os.path.isdir(d):
        return out
    for pt in glob.glob(os.path.join(d, "**", "*.pt"), recursive=True):
        stem = os.path.splitext(os.path.basename(pt))[0].lower()
        out[stem] = os.path.abspath(pt)
    return dict(sorted(out.items()))


def resolve_voice_path(speaker_name: Optional[str]) -> str:
    """
    Match a user-facing id (e.g. 'carter', 'emma') or a stem like 'en-carter_man' to a .pt file.
    Falls back to the first available preset file.
    """
    available = scan_voice_files()
    if not available:
        raise FileNotFoundError(
            f"No voice .pt files found under {_voices_dir()}. "
            "Run: python scripts/download_voices.py"
        )

    if not speaker_name:
        speaker_name = DEFAULT_VOICE_PRESETS[0].id

    key = speaker_name.strip().lower()

    # Exact stem match
    if key in available:
        return available[key]

    # Preset id -> filename
    for preset in DEFAULT_VOICE_PRESETS:
        if preset.id == key:
            stem = os.path.splitext(preset.filename)[0].lower()
            if stem in available:
                return available[stem]
            path = os.path.join(_voices_dir(), preset.filename)
            if os.path.isfile(path):
                return os.path.abspath(path)

    # Substring match (one match only)
    matches = [p for stem, p in available.items() if key in stem or stem in key]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous voice '{speaker_name}'; use a preset id: {[p.id for p in DEFAULT_VOICE_PRESETS]}")

    # Default: first alphabetically
    return next(iter(available.values()))


def list_voices() -> List[Dict[str, str]]:
    """API-friendly list: presets plus any extra scanned voices."""
    scanned = scan_voice_files()
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
        rows.append({"id": stem, "label": stem.replace("-", " ").title(), "available": "True", "filename": os.path.basename(path)})
    return rows
