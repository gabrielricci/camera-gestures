import bus
import context
import hue


class TurnOnOfficeLights:
    _light_ids = [5, 6]
    _color_default = {"hue": 14922, "sat": 144, "bri": 254, "transitiontime": 20}

    def execute(self) -> None:
        bridge = context.get("hue_bridge")
        hue.turn_on(bridge, self._light_ids)
        hue.set_color(bridge, self._light_ids, self._color_default)
        bus.emit("lights_changed", light_ids=self._light_ids)
