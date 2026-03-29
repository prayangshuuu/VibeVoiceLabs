"""Lazy model load/unload with a simple memory budget (simulated pressure)."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

from services.models.registry import MODELS, ModelEntry

logger = logging.getLogger("vibevoice.models.manager")


class ModelManager:
    def __init__(self, *, memory_budget_gb: float = 24.0) -> None:
        self._memory_budget_gb = memory_budget_gb
        self._loaded: Dict[str, Any] = {}
        self._load_order: List[str] = []
        self._lock = threading.Lock()

    def _memory_used_unlocked(self) -> float:
        total = 0.0
        for name in self._loaded:
            entry = MODELS.get(name)
            if entry:
                total += float(entry.get("memory_cost_gb", 0.0))
        return total

    def _evict_under_pressure(self, need_gb: float) -> None:
        """Unload ASR models first, then newest, until under budget or only TTS remains."""
        with self._lock:
            while self._loaded and self._memory_used_unlocked() + need_gb > self._memory_budget_gb:
                victim: Optional[str] = None
                for name in reversed(self._load_order):
                    meta = MODELS.get(name)
                    if meta and meta.get("type") == "asr":
                        victim = name
                        break
                if victim is None and len(self._load_order) > 1:
                    for name in reversed(self._load_order):
                        if name != "tts_realtime":
                            victim = name
                            break
                if victim is None:
                    break
                self._unload_unlocked(victim)

    def _unload_unlocked(self, name: str) -> None:
        if name not in self._loaded:
            return
        logger.info("Unloading model %s (memory pressure or explicit)", name)
        del self._loaded[name]
        self._load_order = [n for n in self._load_order if n != name]

    def load_model(self, name: str) -> Any:
        with self._lock:
            if name in self._loaded:
                return self._loaded[name]
        entry: Optional[ModelEntry] = MODELS.get(name)
        if entry is None:
            raise KeyError(f"Unknown model: {name}")
        need = float(entry.get("memory_cost_gb", 0.0))
        self._evict_under_pressure(need)
        loader = entry.get("loader")
        if loader is None:
            raise RuntimeError(f"Model {name} has no loader")
        logger.info("Loading model %s (%s)", name, entry.get("name", name))
        obj = loader()
        if obj is None:
            raise RuntimeError(f"Model {name} loader returned None (unavailable)")
        with self._lock:
            if name in self._loaded:
                return self._loaded[name]
            self._loaded[name] = obj
            self._load_order.append(name)
            return obj

    def load_if_available(self, name: str) -> Optional[Any]:
        """Load and register model, or return None if loader yields None (e.g. ASR-7B off)."""
        with self._lock:
            if name in self._loaded:
                return self._loaded[name]
        entry: Optional[ModelEntry] = MODELS.get(name)
        if entry is None:
            return None
        loader = entry.get("loader")
        if loader is None:
            return None
        need = float(entry.get("memory_cost_gb", 0.0))
        self._evict_under_pressure(need)
        obj = loader()
        if obj is None:
            return None
        with self._lock:
            if name in self._loaded:
                return self._loaded[name]
            self._loaded[name] = obj
            self._load_order.append(name)
            return obj

    def unload_model(self, name: str) -> None:
        with self._lock:
            self._unload_unlocked(name)

    def get_model(self, name: str) -> Optional[Any]:
        with self._lock:
            return self._loaded.get(name)

    def ensure_tts(self) -> Any:
        """TTS is expected to be loaded at startup; manager returns the live handle."""
        return self.load_model("tts_realtime")

    def list_active(self) -> List[str]:
        with self._lock:
            return list(self._load_order)
