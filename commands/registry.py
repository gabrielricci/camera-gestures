from __future__ import annotations

import yaml

from commands.base import Command
from commands.fallback import FallbackCommand
from commands.hue_turn_on_lights import HueTurnOnLights
from commands.hue_turn_off_lights import HueTurnOffLights
from commands.tuya_press_key_infrared_ac import TuyaPressKeyInfraredAC

COMMAND_CLASSES = {
    "HueTurnOnLights": HueTurnOnLights,
    "HueTurnOffLights": HueTurnOffLights,
    "TuyaPressKeyInfraredAC": TuyaPressKeyInfraredAC,
}


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

    @classmethod
    def build_from_yaml(
        cls, path: str, enabled_integrations: set[str]
    ) -> "CommandRegistry":
        registry = cls()
        with open(path) as f:
            gestures = yaml.safe_load(f).get("gestures", {})
        for gesture, cfg in gestures.items():
            integration = cfg.get("integration")
            if integration and integration not in enabled_integrations:
                print(f"[gestures] Skipping '{gesture}': {integration} disabled")
                continue
            command_cls = COMMAND_CLASSES.get(cfg["command"])
            if command_cls is None:
                print(
                    f"[gestures] Unknown command '{cfg['command']}' for '{gesture}', skipping"
                )
                continue
            registry.register(gesture, command_cls(**cfg.get("params", {})))
        return registry
