from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Hook(Protocol):
    """Interface for lifecycle hooks."""

    def on_enter_command_mode(self) -> None:
        """Called once when transitioning into COMMAND_MODE."""
        ...

    def on_exit_command_mode(self) -> None:
        """Called once when leaving COMMAND_MODE (timeout or command run)."""
        ...

    def on_frame(self, frame: np.ndarray, in_command_mode: bool) -> None:
        """Called every frame — use for visual overlays."""
        ...
