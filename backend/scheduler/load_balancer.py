"""Pick the least-loaded worker node (simulated cluster)."""

from __future__ import annotations

from typing import Iterable, List, TypeVar

T = TypeVar("T")


def pick_least_loaded(nodes: Iterable[T], *, load_key) -> T:
    nodes_list: List[T] = list(nodes)
    if not nodes_list:
        raise RuntimeError("No worker nodes available")
    return min(nodes_list, key=load_key)
