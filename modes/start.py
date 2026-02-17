"""Start mode — launch the gesture listener."""

import time

import cv2

import context
import config
import integrations
from state_machine import State, StateMachine
from gestures.detector import HandDetector
from commands.registry import CommandRegistry
from commands import TurnOffOfficeLights, TurnOnOfficeLights
from hooks.console_hook import ConsoleHook
from hooks.hue_hook import HueHook
from controller import GestureController
from hue import get_bridge


def build_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register("fingers_extended:index+middle", TurnOffOfficeLights())
    registry.register("fingers_extended:index", TurnOnOfficeLights())
    return registry


def run() -> None:
    hue_cfg = integrations.get("hue")

    if hue_cfg.get("enabled"):
        bridge = get_bridge()
        context.register("hue_bridge", bridge)
    else:
        print("Hue Integration disabled — skipping")

    sm = StateMachine()
    registry = build_registry()

    hooks = [ConsoleHook()]
    if hue_cfg.get("enabled"):
        hooks.append(HueHook(hue_cfg["office_light_ids"]))
    if config.GUI_ENABLED:
        from hooks.overlay_hook import OverlayHook

        hooks.append(OverlayHook())

    controller = GestureController(sm, registry, hooks)

    detector = HandDetector(
        max_hands=config.MEDIAPIPE_MAX_HANDS,
        min_detection_confidence=config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
    )

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("ERROR: cannot open camera")
        return

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            results = detector.process(frame)
            now = time.monotonic()

            hand_landmarks = None
            if results.hand_landmarks:
                hand_landmarks = results.hand_landmarks[0]

            if config.GUI_ENABLED and hand_landmarks:
                detector.draw_landmarks(frame, hand_landmarks)

            controller.handle_frame(now, hand_landmarks)

            in_command_mode = sm.state == State.COMMAND_MODE
            for hook in hooks:
                hook.on_frame(frame, in_command_mode)

            if config.GUI_ENABLED:
                cv2.imshow("Gesture Control", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                time.sleep(0.001)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        detector.close()
        cap.release()
        if config.GUI_ENABLED:
            cv2.destroyAllWindows()
