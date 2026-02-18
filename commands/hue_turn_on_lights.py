import bus
import context
from integrations import hue


class HueTurnOnLights:
    def __init__(self, light_ids: list, color: dict = None):
        self._light_ids = light_ids
        self._color = color or {}

    def execute(self) -> None:
        bridge = context.get("hue_bridge")
        hue.turn_on(bridge, self._light_ids)
        if self._color:
            hue.set_color(bridge, self._light_ids, self._color)
        bus.emit("lights_changed", light_ids=self._light_ids)
