"""Multi-speaker dialogue validation."""

from __future__ import annotations

from services.inference.generation import parse_multi_speaker


def unique_speaker_count(text: str) -> int:
    turns = parse_multi_speaker(text)
    return len({t.speaker for t in turns})


def assert_max_speakers(text: str, max_speakers: int = 4) -> None:
    n = unique_speaker_count(text)
    if n > max_speakers:
        raise ValueError(f"Too many distinct speakers ({n}); maximum supported is {max_speakers}.")
