import bus
import context
from integrations import hue


class HueTurnOffLights:
    def __init__(self, light_ids: list):
        self._light_ids = light_ids

    def execute(self) -> None:
        bridge = context.get("hue_bridge")
        hue.turn_off(bridge, self._light_ids)
        bus.emit("lights_changed", light_ids=self._light_ids)
