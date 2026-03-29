"""Lightweight ASR backends (no heavy deps required for local runs)."""

from __future__ import annotations


class MockASRBackend:
    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        n = len(audio_bytes)
        return f"[mock-asr] placeholder transcript — {n} bytes from {filename!r}"
