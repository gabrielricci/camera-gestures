"""Load and persist integrations.yaml."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

_FILE = Path(os.path.dirname(__file__)).parent / "integrations.yaml"

_cache: dict | None = None


def load() -> dict:
    global _cache
    if _cache is None:
        if not _FILE.exists():
            print(f"[integrations] {_FILE.name} not found — creating empty file")
            _FILE.touch()
        with open(_FILE) as f:
            _cache = yaml.safe_load(f) or {}
    return _cache


def save() -> None:
    with open(_FILE, "w") as f:
        yaml.dump(_cache, f, default_flow_style=False)


def get(integration: str, default={}) -> dict:
    return load().get(integration, default)


def update(integration: str, **kwargs) -> None:
    data = load()

    if not data.get(integration):
        data[integration] = {}

    data[integration].update(kwargs)
    save()
