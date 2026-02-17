"""Lightweight synchronous event bus.

    import bus
    bus.on("lights_changed", lambda light_ids: ...)
    bus.emit("lights_changed", light_ids=[4, 5])
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

_listeners: dict[str, list[Callable]] = defaultdict(list)


def on(event: str, callback: Callable) -> None:
    _listeners[event].append(callback)


def off(event: str, callback: Callable) -> None:
    _listeners[event].remove(callback)


def emit(event: str, **kwargs) -> None:
    for cb in _listeners[event]:
        cb(**kwargs)
