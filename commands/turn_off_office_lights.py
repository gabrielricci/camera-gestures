import bus
import context
import hue


class TurnOffOfficeLights:
    _light_ids = [5, 6]
    _color_green = {"hue": 25500, "sat": 100, "bri": 100, "transitiontime": 5}

    def execute(self) -> None:
        bridge = context.get("hue_bridge")
        hue.turn_off(bridge, self._light_ids)
        bus.emit("lights_changed", light_ids=self._light_ids)
