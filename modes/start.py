"""Start mode — launch the gesture listener."""

import time

import cv2

import config
import integrations
from integrations import hue, tuya
from state_machine import State, StateMachine
from gestures.detector import HandDetector
from commands.registry import CommandRegistry
from hooks import build_from_yaml as build_hooks
from controller import GestureController


def run() -> None:
    enabled_integrations: set[str] = set()

    hue_cfg = integrations.get("hue")
    if hue_cfg.get("enabled"):
        hue.init()
        enabled_integrations.add("hue")
    else:
        print("Hue Integration disabled — skipping")

    tuya_cfg = integrations.get("tuya")
    if tuya_cfg and tuya_cfg.get("enabled", False):
        tuya.init()
        enabled_integrations.add("tuya")
    else:
        print("Tuya Integration disabled — skipping")

    sm = StateMachine()
    registry = CommandRegistry.build_from_yaml("gestures.yaml", enabled_integrations)
    hooks = build_hooks("gestures.yaml", enabled_integrations)

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
