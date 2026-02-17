import cv2
import numpy as np

BORDER_THICKNESS = 8
BORDER_COLOR = (0, 255, 0)  # green in BGR


class OverlayHook:
    def on_enter_command_mode(self) -> None:
        pass

    def on_exit_command_mode(self) -> None:
        pass

    def on_frame(self, frame: np.ndarray, in_command_mode: bool) -> None:
        if in_command_mode:
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0, 0), (w, h), BORDER_COLOR, BORDER_THICKNESS)
