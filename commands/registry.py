from __future__ import annotations

from commands.base import Command
from commands.fallback import FallbackCommand


class CommandRegistry:
    """Maps gesture names to Command instances."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, gesture: str, command: Command) -> None:
        self._commands[gesture] = command

    def resolve(self, gesture_name: str) -> Command:
        if gesture_name in self._commands:
            return self._commands[gesture_name]

        return FallbackCommand(gesture_name)
