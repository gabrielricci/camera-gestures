"""Hue hook — visual feedback via office lights during command mode.

On enter: snapshots the current light state, then fades to blue.
On settle (after any command has run, or on timeout): restores the
snapshot, skipping lights that were already changed by the command.
"""

from __future__ import annotations

import numpy as np

import bus
import context
import integrations


class HueHook:
    def __init__(self, light_ids: list[int]) -> None:
        self._light_ids = light_ids
        hue_cfg = integrations.get("hue")
        self._command_mode_hue = hue_cfg["command_mode_hue"]
        self._command_mode_transition = hue_cfg["command_mode_transition"]
        self._snapshot: dict[int, dict] = {}
        self._changed_by_command: set[int] = set()

        bus.on("lights_changed", self._on_lights_changed)
        bus.on("command_mode_settled", self._on_settled)

    def on_enter_command_mode(self) -> None:
        bridge = context.get("hue_bridge")
        self._snapshot = {}
        self._changed_by_command = set()

        for lid in self._light_ids:
            state = bridge.get_light(lid)["state"]
            self._snapshot[lid] = {
                "on": state["on"],
                "bri": state.get("bri", 254),
                "hue": state.get("hue"),
                "sat": state.get("sat"),
                "ct": state.get("ct"),
                "colormode": state.get("colormode"),
            }

        cmd = {
            "on": True,
            "hue": self._command_mode_hue,
            "sat": 254,
            "bri": 100,
            "transitiontime": self._command_mode_transition,
        }
        for lid in self._light_ids:
            bridge.set_light(lid, cmd)

    def on_exit_command_mode(self) -> None:
        pass  # actual restore is deferred to "command_mode_settled"

    def on_frame(self, frame: np.ndarray, in_command_mode: bool) -> None:
        pass

    # -- bus listeners --

    def _on_lights_changed(self, light_ids: list[int]) -> None:
        self._changed_by_command.update(light_ids)

    def _on_settled(self) -> None:
        if not self._snapshot:
            return

        bridge = context.get("hue_bridge")
        for lid in self._light_ids:
            if lid in self._changed_by_command:
                continue
            saved = self._snapshot.get(lid)
            if not saved:
                continue
            restore = {"transitiontime": 10}  # 1-second fade back
            if not saved["on"]:
                restore["on"] = False
            else:
                restore["on"] = True
                restore["bri"] = saved["bri"]
                if saved["colormode"] == "hs" and saved["hue"] is not None:
                    restore["hue"] = saved["hue"]
                    restore["sat"] = saved["sat"]
                elif saved["colormode"] == "ct" and saved["ct"] is not None:
                    restore["ct"] = saved["ct"]
            bridge.set_light(lid, restore)

        [l for l in self._light_ids if l not in self._changed_by_command]

        self._snapshot = {}
        self._changed_by_command = set()
