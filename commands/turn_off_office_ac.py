import context
import tuya


class TurnOffOfficeAc:
    def execute(self) -> None:
        tuya.turn_off_ir_ac(context.get("tuya_cloud"), "ar_da_sala")
