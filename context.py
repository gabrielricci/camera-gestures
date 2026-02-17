"""Global service registry.

Register shared dependencies (e.g. the Hue bridge) once at startup, then
look them up from anywhere — hooks, commands, etc.

    import context
    context.register("bridge", bridge)
    ...
    bridge = context.get("bridge")
"""

from __future__ import annotations

_services: dict[str, object] = {}


def register(name: str, service: object) -> None:
    _services[name] = service


def get(name: str) -> object:
    return _services[name]
