from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Command(Protocol):
    """Interface every command must satisfy."""

    def execute(self) -> None:
        """Run the command.  May block briefly (e.g. HTTP call)."""
        ...
