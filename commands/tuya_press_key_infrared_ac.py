import context
from integrations import tuya


class TuyaPressKeyInfraredAC:
    def __init__(self, device: str, key: str):
        self._device = device
        self._key = key

    def execute(self) -> None:
        tuya.press_key_ir_ac(context.get("tuya_cloud"), self._device, self._key)
