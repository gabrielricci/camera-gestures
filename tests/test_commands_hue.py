from unittest.mock import MagicMock, patch, call

import bus
import context
from commands.hue_turn_on_lights import HueTurnOnLights
from commands.hue_turn_off_lights import HueTurnOffLights


@patch("commands.hue_turn_on_lights.hue")
def test_turn_on_calls_hue_turn_on(mock_hue):
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    cmd = HueTurnOnLights(light_ids=[5, 6])
    cmd.execute()
    mock_hue.turn_on.assert_called_once_with(bridge, [5, 6])


@patch("commands.hue_turn_on_lights.hue")
def test_turn_on_with_color_calls_set_color(mock_hue):
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    color = {"hue": 14922, "sat": 144, "bri": 254}
    cmd = HueTurnOnLights(light_ids=[5, 6], color=color)
    cmd.execute()
    mock_hue.set_color.assert_called_once_with(bridge, [5, 6], color)


@patch("commands.hue_turn_on_lights.hue")
def test_turn_on_without_color_skips_set_color(mock_hue):
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    cmd = HueTurnOnLights(light_ids=[5, 6])
    cmd.execute()
    mock_hue.set_color.assert_not_called()


@patch("commands.hue_turn_on_lights.hue")
def test_turn_on_emits_lights_changed(mock_hue):
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    received = []
    bus.on("lights_changed", lambda **kw: received.append(kw))
    cmd = HueTurnOnLights(light_ids=[5, 6])
    cmd.execute()
    assert received == [{"light_ids": [5, 6]}]


@patch("commands.hue_turn_off_lights.hue")
def test_turn_off_calls_hue_turn_off(mock_hue):
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    cmd = HueTurnOffLights(light_ids=[5, 6])
    cmd.execute()
    mock_hue.turn_off.assert_called_once_with(bridge, [5, 6])


@patch("commands.hue_turn_off_lights.hue")
def test_turn_off_emits_lights_changed(mock_hue):
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    received = []
    bus.on("lights_changed", lambda **kw: received.append(kw))
    cmd = HueTurnOffLights(light_ids=[3])
    cmd.execute()
    assert received == [{"light_ids": [3]}]
