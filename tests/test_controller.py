"""Tests for GestureController frame-by-frame logic.

All external collaborators (gesture recognizer, config values, registry,
hooks) are mocked so tests exercise only the controller's state transitions
and timing logic.
"""

from unittest.mock import MagicMock, patch, call
import pytest

import bus
import config
from state_machine import State, StateMachine
from controller import GestureController


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sm():
    return StateMachine()


@pytest.fixture
def registry():
    reg = MagicMock()
    reg.resolve.return_value = MagicMock()  # default: a no-op command
    return reg


@pytest.fixture
def hook():
    h = MagicMock()
    h.on_enter_command_mode = MagicMock()
    h.on_exit_command_mode = MagicMock()
    return h


@pytest.fixture
def controller(sm, registry, hook):
    return GestureController(sm, registry, [hook])


# Patch config timing so tests don't depend on real config.yaml values
@pytest.fixture(autouse=True)
def fast_config(monkeypatch):
    monkeypatch.setattr(config, "WAKE_HOLD_SECONDS", 1.0)
    monkeypatch.setattr(config, "COMMAND_HOLD_SECONDS", 1.0)
    monkeypatch.setattr(config, "COMMAND_TIMEOUT_SECONDS", 5.0)
    monkeypatch.setattr(config, "COMMAND_DEBOUNCE_SECONDS", 2.0)


# ---------------------------------------------------------------------------
# Helper to drive the controller with a fixed gesture string
# ---------------------------------------------------------------------------

def drive(controller, gesture, now, recognize_path="controller.recognize",
          wake_path="controller.is_wake_gesture"):
    with patch(recognize_path, return_value=gesture), \
         patch(wake_path, side_effect=lambda g: g == "closed_fist"):
        controller.handle_frame(now, object())


# ---------------------------------------------------------------------------
# IDLE state tests
# ---------------------------------------------------------------------------

def test_idle_no_hand_stays_idle(controller, sm):
    drive(controller, "no_hand", now=0.0)
    assert sm.state == State.IDLE


def test_idle_wake_gesture_not_held_long_enough_stays_idle(controller, sm):
    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=0.5)  # only 0.5 s < 1.0 s threshold
    assert sm.state == State.IDLE


def test_idle_wake_gesture_held_enters_command_mode(controller, sm, hook):
    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)
    assert sm.state == State.COMMAND_MODE
    hook.on_enter_command_mode.assert_called_once()


def test_idle_wake_gesture_interrupted_resets_timer(controller, sm):
    drive(controller, "closed_fist", now=0.0)
    drive(controller, "no_hand", now=0.5)       # interrupt
    drive(controller, "closed_fist", now=0.6)   # restart
    drive(controller, "closed_fist", now=1.4)   # only 0.8 s since restart
    assert sm.state == State.IDLE


# ---------------------------------------------------------------------------
# COMMAND_MODE timeout
# ---------------------------------------------------------------------------

def test_command_mode_timeout_returns_to_idle(controller, sm, hook):
    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)   # enter command mode at t=1.1
    assert sm.state == State.COMMAND_MODE

    drive(controller, "no_hand", now=7.0)        # 5.9 s later > 5 s timeout
    assert sm.state == State.IDLE
    hook.on_exit_command_mode.assert_called_once()


def test_command_mode_timeout_emits_settled(controller, sm):
    settled = []
    bus.on("command_mode_settled", lambda **kw: settled.append(True))

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)
    drive(controller, "no_hand", now=7.0)

    assert settled == [True]


# ---------------------------------------------------------------------------
# Command recognition and execution
# ---------------------------------------------------------------------------

def test_command_gesture_held_executes_command(controller, sm, registry):
    command = MagicMock()
    registry.resolve.return_value = command

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)   # enter command mode

    # Tracking must start at now >= 2.0 so the initial debounce window has passed
    drive(controller, "fingers_extended:index", now=3.0)   # start tracking
    drive(controller, "fingers_extended:index", now=4.1)   # held 1.1 s > 1.0 s threshold

    command.execute.assert_called_once()
    assert sm.state == State.IDLE


def test_command_gesture_not_held_long_enough_does_not_execute(controller, sm, registry):
    command = MagicMock()
    registry.resolve.return_value = command

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)

    drive(controller, "fingers_extended:index", now=3.0)   # start tracking
    drive(controller, "fingers_extended:index", now=3.7)   # only 0.7 s < 1.0 s

    command.execute.assert_not_called()
    assert sm.state == State.COMMAND_MODE


def test_changing_gesture_resets_hold_timer(controller, sm, registry):
    command = MagicMock()
    registry.resolve.return_value = command

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)

    drive(controller, "fingers_extended:index", now=3.0)   # start tracking A
    drive(controller, "fingers_extended:middle", now=3.5)  # switch to B — timer resets
    drive(controller, "fingers_extended:middle", now=4.6)  # held B for 1.1 s → executes

    command.execute.assert_called_once()
    registry.resolve.assert_called_with("fingers_extended:middle")


def test_command_execution_returns_to_idle_and_emits_settled(controller, sm):
    settled = []
    bus.on("command_mode_settled", lambda **kw: settled.append(True))

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)
    drive(controller, "fingers_extended:index", now=3.0)
    drive(controller, "fingers_extended:index", now=4.1)

    assert sm.state == State.IDLE
    assert settled == [True]


def test_hook_notified_on_command_exit(controller, sm, hook):
    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)
    drive(controller, "fingers_extended:index", now=3.0)
    drive(controller, "fingers_extended:index", now=4.1)

    hook.on_exit_command_mode.assert_called_once()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_command_exception_still_returns_to_idle(controller, sm, registry):
    command = MagicMock()
    command.execute.side_effect = RuntimeError("boom")
    registry.resolve.return_value = command

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)
    drive(controller, "fingers_extended:index", now=3.0)
    drive(controller, "fingers_extended:index", now=4.1)

    assert sm.state == State.IDLE


def test_command_exception_still_emits_settled(controller, sm, registry):
    settled = []
    bus.on("command_mode_settled", lambda **kw: settled.append(True))

    command = MagicMock()
    command.execute.side_effect = RuntimeError("boom")
    registry.resolve.return_value = command

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)
    drive(controller, "fingers_extended:index", now=3.0)
    drive(controller, "fingers_extended:index", now=4.1)

    assert settled == [True]


# ---------------------------------------------------------------------------
# Debounce
# ---------------------------------------------------------------------------

def test_debounce_blocks_command_within_debounce_window(controller, sm, registry):
    command = MagicMock()
    registry.resolve.return_value = command

    # Simulate a command that just ran at t=10.0
    controller._last_command_at = 10.0

    drive(controller, "closed_fist", now=10.0)
    drive(controller, "closed_fist", now=11.1)   # enter command mode

    # Attempt to run within the 2.0 s debounce window
    drive(controller, "fingers_extended:index", now=11.5)  # 1.5 s < 2.0 s → blocked
    drive(controller, "fingers_extended:index", now=11.9)  # 1.9 s < 2.0 s → blocked

    command.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Wake gesture in command mode resets command tracking
# ---------------------------------------------------------------------------

def test_wake_gesture_in_command_mode_resets_command_tracking(controller, sm, registry):
    """Holding a gesture 0.4 s, interrupting with a wake gesture, then holding
    the same gesture for only 0.8 s more must NOT execute — the timer resets."""
    command = MagicMock()
    registry.resolve.return_value = command

    drive(controller, "closed_fist", now=0.0)
    drive(controller, "closed_fist", now=1.1)

    drive(controller, "fingers_extended:index", now=3.0)  # track for 0.4 s
    drive(controller, "closed_fist", now=3.4)             # wake gesture → timer reset
    drive(controller, "fingers_extended:index", now=3.5)  # restart tracking from here
    drive(controller, "fingers_extended:index", now=4.3)  # 0.8 s since reset < 1.0 s

    command.execute.assert_not_called()
