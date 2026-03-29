"""Bounded in-memory caches for generations and voice tensors."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from threading import Lock
from typing import Any, Callable, Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, max_entries: int) -> None:
        self.max_entries = max_entries
        self._data: OrderedDict[K, V] = OrderedDict()
        self._lock = Lock()

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def set(self, key: K, value: V) -> None:
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)


def tts_cache_key(
    text: str,
    voice: Optional[str],
    multi_speaker: bool,
    cfg_scale: float,
    speaker_voice_map: Optional[dict] = None,
) -> str:
    sm = ""
    if speaker_voice_map:
        sm = "|".join(f"{k}:{v}" for k, v in sorted(speaker_voice_map.items()))
    raw = f"{voice or ''}|{multi_speaker}|{cfg_scale:.4f}|{sm}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class GenerationCache:
    """Cache completed synthesis output paths keyed by content hash."""

    def __init__(self, max_entries: int) -> None:
        self._cache: LRUCache[str, str] = LRUCache(max_entries)

    def get_path(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    def put_path(self, key: str, path: str) -> None:
        self._cache.set(key, path)


class VoiceEmbeddingCache:
    """Cache loaded voice tensors by resolved .pt path (expensive reload avoidance)."""

    def __init__(self, max_entries: int) -> None:
        self._cache: LRUCache[str, Any] = LRUCache(max_entries)

    def get_or_load(self, voice_path: str, loader: Callable[[], Any]) -> Any:
        hit = self._cache.get(voice_path)
        if hit is not None:
            return hit
        value = loader()
        self._cache.set(voice_path, value)
        return value
