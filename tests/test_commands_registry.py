import pytest
import yaml

from commands.registry import CommandRegistry
from commands.fallback import FallbackCommand
from commands.hue_turn_on_lights import HueTurnOnLights
from commands.hue_turn_off_lights import HueTurnOffLights
from commands.tuya_press_key_infrared_ac import TuyaPressKeyInfraredAC


GESTURES_YAML = {
    "gestures": {
        "fingers_extended:index": {
            "command": "HueTurnOnLights",
            "integration": "hue",
            "params": {"light_ids": [1, 2], "color": {"hue": 100}},
        },
        "fingers_extended:index+middle": {
            "command": "HueTurnOffLights",
            "integration": "hue",
            "params": {"light_ids": [1, 2]},
        },
        "fingers_extended:thumb+pinky": {
            "command": "TuyaPressKeyInfraredAC",
            "integration": "tuya",
            "params": {"device": "ac_unit", "key": "PowerOn"},
        },
    }
}


@pytest.fixture
def gestures_file(tmp_path):
    path = tmp_path / "gestures.yaml"
    path.write_text(yaml.dump(GESTURES_YAML))
    return str(path)


# ---------------------------------------------------------------------------
# Direct register / resolve
# ---------------------------------------------------------------------------

def test_resolve_registered_gesture():
    registry = CommandRegistry()
    cmd = HueTurnOffLights(light_ids=[1])
    registry.register("fingers_extended:index+middle", cmd)
    assert registry.resolve("fingers_extended:index+middle") is cmd


def test_resolve_unknown_gesture_returns_fallback():
    registry = CommandRegistry()
    result = registry.resolve("unknown_gesture")
    assert isinstance(result, FallbackCommand)


# ---------------------------------------------------------------------------
# build_from_yaml
# ---------------------------------------------------------------------------

def test_build_all_integrations_enabled(gestures_file):
    registry = CommandRegistry.build_from_yaml(gestures_file, {"hue", "tuya"})
    assert isinstance(registry.resolve("fingers_extended:index"), HueTurnOnLights)
    assert isinstance(registry.resolve("fingers_extended:index+middle"), HueTurnOffLights)
    assert isinstance(registry.resolve("fingers_extended:thumb+pinky"), TuyaPressKeyInfraredAC)


def test_build_disabled_integration_skipped(gestures_file):
    registry = CommandRegistry.build_from_yaml(gestures_file, {"hue"})
    assert isinstance(registry.resolve("fingers_extended:index"), HueTurnOnLights)
    assert isinstance(registry.resolve("fingers_extended:thumb+pinky"), FallbackCommand)


def test_build_no_integrations_enabled_all_skipped(gestures_file):
    registry = CommandRegistry.build_from_yaml(gestures_file, set())
    assert isinstance(registry.resolve("fingers_extended:index"), FallbackCommand)
    assert isinstance(registry.resolve("fingers_extended:index+middle"), FallbackCommand)
    assert isinstance(registry.resolve("fingers_extended:thumb+pinky"), FallbackCommand)


def test_build_unknown_command_name_skipped(tmp_path):
    data = {"gestures": {"some_gesture": {"command": "NonExistentCommand", "params": {}}}}
    path = tmp_path / "gestures.yaml"
    path.write_text(yaml.dump(data))
    registry = CommandRegistry.build_from_yaml(str(path), set())
    assert isinstance(registry.resolve("some_gesture"), FallbackCommand)


def test_build_params_passed_to_command(gestures_file):
    registry = CommandRegistry.build_from_yaml(gestures_file, {"hue", "tuya"})
    cmd = registry.resolve("fingers_extended:thumb+pinky")
    assert isinstance(cmd, TuyaPressKeyInfraredAC)
    assert cmd._device == "ac_unit"
    assert cmd._key == "PowerOn"


def test_build_empty_gestures_section(tmp_path):
    data = {"gestures": {}}
    path = tmp_path / "gestures.yaml"
    path.write_text(yaml.dump(data))
    registry = CommandRegistry.build_from_yaml(str(path), {"hue"})
    assert isinstance(registry.resolve("anything"), FallbackCommand)
