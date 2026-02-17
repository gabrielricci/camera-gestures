"""GestureController — encapsulates per-frame gesture logic."""

from __future__ import annotations
from typing import Optional

import time

import bus
import config
from state_machine import State, StateMachine
from gestures.wake_gesture import is_wake_gesture
from gestures.recognizer import recognize
from commands.registry import CommandRegistry
from hooks.base import Hook


class GestureController:
    def __init__(
        self,
        sm: StateMachine,
        registry: CommandRegistry,
        hooks: list[Hook],
    ) -> None:
        self._sm = sm
        self._registry = registry
        self._hooks = hooks

        self._wake_gesture_start: float | None = None
        self._command_mode_entered_at: float | None = None
        self._last_command_at: float = 0.0
        self._command_gesture_name: str | None = None
        self._command_gesture_start: float | None = None

    def handle_frame(self, now: float, hand_landmarks: Optional[list]) -> None:
        gesture = recognize(hand_landmarks)

        if self._sm.state == State.IDLE:
            self._handle_idle(gesture, now)
        elif self._sm.state == State.COMMAND_MODE:
            self._handle_command_mode(gesture, now)

    def _handle_idle(self, gesture: str | None, now: float) -> None:
        if is_wake_gesture(gesture):
            print("wake gesture")
            if self._wake_gesture_start is None:
                self._wake_gesture_start = now
            elif now - self._wake_gesture_start >= config.WAKE_HOLD_SECONDS:
                self._sm.transition_to(State.COMMAND_MODE)
                self._command_mode_entered_at = now
                self._wake_gesture_start = None
                self._notify_hooks("on_enter_command_mode")
        else:
            self._wake_gesture_start = None

    def _handle_command_mode(self, gesture: str | None, now: float) -> None:
        timed_out = (
            self._command_mode_entered_at is not None
            and now - self._command_mode_entered_at >= config.COMMAND_TIMEOUT_SECONDS
        )
        if timed_out:
            print("[timeout] No command detected, returning to IDLE")
            self._sm.transition_to(State.IDLE)
            self._notify_hooks("on_exit_command_mode")
            bus.emit("command_mode_settled")
            return

        if is_wake_gesture(gesture):
            self._command_gesture_name = None
            self._command_gesture_start = None
            return

        if not gesture or now - self._last_command_at < config.COMMAND_DEBOUNCE_SECONDS:
            self._command_gesture_name = None
            self._command_gesture_start = None
            return

        if gesture == self._command_gesture_name:
            if (
                self._command_gesture_start is not None
                and now - self._command_gesture_start >= config.COMMAND_HOLD_SECONDS
            ):
                command = self._registry.resolve(gesture)
                self._sm.transition_to(State.RUNNING_COMMAND)
                self._notify_hooks("on_exit_command_mode")

                self._command_gesture_name = None
                self._command_gesture_start = None
                try:
                    command.execute()
                except Exception as exc:
                    print(f"[error] Command failed: {exc}")
                finally:
                    self._last_command_at = time.monotonic()
                    self._sm.transition_to(State.IDLE)
                    bus.emit("command_mode_settled")
        else:
            self._command_gesture_name = gesture
            self._command_gesture_start = now

    def _notify_hooks(self, method_name: str) -> None:
        for hook in self._hooks:
            getattr(hook, method_name)()
