import os

import mediapipe as mp
import cv2
import numpy as np

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Standard MediaPipe hand connections for drawing.
HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # index
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # middle  (fixed: 0→9 via 5→9)
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # ring    (fixed: 0→13 via 9→13)
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # pinky
    (5, 9),
    (9, 13),
    (13, 17),  # palm
]

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "hand_landmarker.task"
)


class HandDetector:
    """Wraps the MediaPipe Tasks HandLandmarker (VIDEO mode)."""

    def __init__(
        self,
        max_hands: int,
        min_detection_confidence: float,
        min_tracking_confidence: float,
    ):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Download it with:\n"
                "  wget -q https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._frame_ts = 0

    def process(self, frame: np.ndarray):
        """Process a BGR frame and return a HandLandmarkerResult."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._frame_ts += 1
        return self._landmarker.detect_for_video(mp_image, self._frame_ts)

    def draw_landmarks(self, frame: np.ndarray, landmarks: list) -> None:
        """Draw hand landmarks and connections on the frame."""
        h, w = frame.shape[:2]
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, points[start], points[end], (0, 255, 0), 2)

        for pt in points:
            cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    def close(self) -> None:
        self._landmarker.close()
