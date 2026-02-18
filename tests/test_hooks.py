import numpy as np
import pytest
import yaml
from unittest.mock import MagicMock, patch, call

import bus
import context
from hooks import build_from_yaml
from hooks.console_hook import ConsoleHook
from hooks.overlay_hook import OverlayHook
from hooks.hue_hook import HueHook


HOOKS_YAML = {
    "hooks": [
        {"hook": "ConsoleHook"},
        {"hook": "HueHook", "integration": "hue", "params": {
            "light_ids": [5, 6], "hue": 46920, "sat": 254, "bri": 100, "transition": 2
        }},
        {"hook": "OverlayHook"},
    ]
}


@pytest.fixture
def hooks_file(tmp_path):
    path = tmp_path / "gestures.yaml"
    path.write_text(yaml.dump(HOOKS_YAML))
    return str(path)


# ---------------------------------------------------------------------------
# build_from_yaml
# ---------------------------------------------------------------------------

def test_build_all_enabled(hooks_file):
    hooks = build_from_yaml(hooks_file, {"hue"})
    assert len(hooks) == 3
    types = [type(h) for h in hooks]
    assert ConsoleHook in types
    assert HueHook in types
    assert OverlayHook in types


def test_build_disabled_integration_skips_hook(hooks_file):
    hooks = build_from_yaml(hooks_file, set())
    assert len(hooks) == 2
    assert not any(isinstance(h, HueHook) for h in hooks)


def test_build_unknown_hook_skipped(tmp_path):
    data = {"hooks": [{"hook": "NonExistentHook"}]}
    path = tmp_path / "gestures.yaml"
    path.write_text(yaml.dump(data))
    hooks = build_from_yaml(str(path), set())
    assert hooks == []


def test_build_no_hooks_section(tmp_path):
    data = {"gestures": {}}
    path = tmp_path / "gestures.yaml"
    path.write_text(yaml.dump(data))
    hooks = build_from_yaml(str(path), {"hue"})
    assert hooks == []


# ---------------------------------------------------------------------------
# ConsoleHook
# ---------------------------------------------------------------------------

def test_console_hook_methods_do_not_raise():
    hook = ConsoleHook({})
    hook.on_enter_command_mode()
    hook.on_exit_command_mode()
    hook.on_frame(np.zeros((480, 640, 3), dtype=np.uint8), True)


# ---------------------------------------------------------------------------
# OverlayHook
# ---------------------------------------------------------------------------

@patch("hooks.overlay_hook.cv2")
def test_overlay_hook_draws_border_in_command_mode(mock_cv2):
    hook = OverlayHook({})
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    hook.on_frame(frame, in_command_mode=True)
    mock_cv2.rectangle.assert_called_once()


@patch("hooks.overlay_hook.cv2")
def test_overlay_hook_no_draw_outside_command_mode(mock_cv2):
    hook = OverlayHook({})
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    hook.on_frame(frame, in_command_mode=False)
    mock_cv2.rectangle.assert_not_called()


# ---------------------------------------------------------------------------
# HueHook
# ---------------------------------------------------------------------------

HUE_PARAMS = {"light_ids": [5, 6], "hue": 46920, "sat": 254, "bri": 100, "transition": 2}


def _make_bridge(lights_state=None):
    """Return a mock bridge whose get_light returns sensible state dicts."""
    if lights_state is None:
        lights_state = {"on": True, "bri": 200, "hue": 10000, "sat": 100, "ct": None, "colormode": "hs"}
    bridge = MagicMock()
    bridge.get_light.return_value = {"state": lights_state}
    return bridge


def test_hue_hook_enter_snapshots_and_sets_command_color():
    bridge = _make_bridge()
    context.register("hue_bridge", bridge)
    hook = HueHook(HUE_PARAMS)

    hook.on_enter_command_mode()

    # Should have snapshotted both lights
    assert 5 in hook._snapshot
    assert 6 in hook._snapshot
    # Should have set the command-mode colour on both lights
    assert bridge.set_light.call_count == 2
    expected_cmd = {"on": True, "hue": 46920, "sat": 254, "bri": 100, "transitiontime": 2}
    bridge.set_light.assert_any_call(5, expected_cmd)
    bridge.set_light.assert_any_call(6, expected_cmd)


def test_hue_hook_settled_restores_lights():
    bridge = _make_bridge({"on": True, "bri": 200, "hue": 10000, "sat": 100, "ct": None, "colormode": "hs"})
    context.register("hue_bridge", bridge)
    hook = HueHook(HUE_PARAMS)

    hook.on_enter_command_mode()
    bridge.reset_mock()

    bus.emit("command_mode_settled")

    assert bridge.set_light.call_count == 2
    for lid in [5, 6]:
        args = bridge.set_light.call_args_list
        light_calls = [a for a in args if a[0][0] == lid]
        assert len(light_calls) == 1
        restore = light_calls[0][0][1]
        assert restore["hue"] == 10000
        assert restore["sat"] == 100


def test_hue_hook_settled_skips_lights_changed_by_command():
    bridge = _make_bridge()
    context.register("hue_bridge", bridge)
    hook = HueHook(HUE_PARAMS)

    hook.on_enter_command_mode()
    bridge.reset_mock()

    bus.emit("lights_changed", light_ids=[5])  # light 5 was changed by a command
    bus.emit("command_mode_settled")

    # Only light 6 should be restored; light 5 was changed by the command
    calls = [c[0][0] for c in bridge.set_light.call_args_list]
    assert 5 not in calls
    assert 6 in calls


def test_hue_hook_settled_without_snapshot_does_nothing():
    bridge = MagicMock()
    context.register("hue_bridge", bridge)
    hook = HueHook(HUE_PARAMS)

    # Emit settled without ever entering command mode
    bus.emit("command_mode_settled")

    bridge.set_light.assert_not_called()


def test_hue_hook_restores_off_lights():
    bridge = _make_bridge({"on": False, "bri": 0, "hue": None, "sat": None, "ct": None, "colormode": None})
    context.register("hue_bridge", bridge)
    hook = HueHook(HUE_PARAMS)

    hook.on_enter_command_mode()
    bridge.reset_mock()

    bus.emit("command_mode_settled")

    for c in bridge.set_light.call_args_list:
        restore = c[0][1]
        assert restore["on"] is False


def test_hue_hook_snapshot_cleared_after_settle():
    bridge = _make_bridge()
    context.register("hue_bridge", bridge)
    hook = HueHook(HUE_PARAMS)

    hook.on_enter_command_mode()
    bus.emit("command_mode_settled")

    assert hook._snapshot == {}
    assert hook._changed_by_command == set()
