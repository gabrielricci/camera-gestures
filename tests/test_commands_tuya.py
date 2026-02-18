from unittest.mock import MagicMock, patch

import context
from commands.tuya_press_key_infrared_ac import TuyaPressKeyInfraredAC


@patch("commands.tuya_press_key_infrared_ac.tuya")
def test_execute_calls_press_key(mock_tuya):
    cloud = MagicMock()
    context.register("tuya_cloud", cloud)
    cmd = TuyaPressKeyInfraredAC(device="ar_da_sala", key="PowerOn")
    cmd.execute()
    mock_tuya.press_key_ir_ac.assert_called_once_with(cloud, "ar_da_sala", "PowerOn")


@patch("commands.tuya_press_key_infrared_ac.tuya")
def test_execute_uses_correct_key(mock_tuya):
    cloud = MagicMock()
    context.register("tuya_cloud", cloud)
    cmd = TuyaPressKeyInfraredAC(device="ar_da_sala", key="PowerOff")
    cmd.execute()
    mock_tuya.press_key_ir_ac.assert_called_once_with(cloud, "ar_da_sala", "PowerOff")
