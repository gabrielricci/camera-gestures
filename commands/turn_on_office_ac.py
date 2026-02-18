import context
import tuya


class TurnOnOfficeAc:
    def execute(self) -> None:
        tuya.turn_on_ir_ac(context.get("tuya_cloud"), "ar_da_sala")
