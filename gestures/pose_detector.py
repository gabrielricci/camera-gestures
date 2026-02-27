"""PoseDetector — wraps MediaPipe PoseLandmarker (VIDEO mode)."""

from __future__ import annotations

import math
import os

import cv2
import mediapipe as mp
import numpy as np

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_WRIST = 15
RIGHT_WRIST = 16

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "pose_landmarker_lite.task"
)


class PoseDetector:
    def __init__(self, max_poses: int = 4, min_detection_confidence: float = 0.5):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Pose model not found at {MODEL_PATH}. Download it with:\n"
                "  wget -q https://storage.googleapis.com/mediapipe-models/"
                "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
            )
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionRunningMode.VIDEO,
            num_poses=max_poses,
            min_pose_detection_confidence=min_detection_confidence,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)
        self._frame_ts = 0

    def process(self, frame: np.ndarray):
        """Process a BGR frame and return a PoseLandmarkerResult."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._frame_ts += 1
        return self._landmarker.detect_for_video(mp_image, self._frame_ts)

    def neck_y_for_hand(
        self,
        hand_wrist_x: float,
        hand_wrist_y: float,
        pose_result,
        match_threshold: float,
    ) -> float | None:
        """
        Return the neck y-coordinate of the person whose wrist is closest
        to the given hand wrist, or None if no match within match_threshold.

        Neck is approximated as the midpoint between the nose and the
        shoulder midpoint.
        """
        if not pose_result or not pose_result.pose_landmarks:
            return None

        best_neck_y = None
        best_dist = float("inf")

        for person in pose_result.pose_landmarks:
            for wrist_idx in (LEFT_WRIST, RIGHT_WRIST):
                lm = person[wrist_idx]
                dist = math.sqrt(
                    (lm.x - hand_wrist_x) ** 2 + (lm.y - hand_wrist_y) ** 2
                )
                if dist < best_dist:
                    best_dist = dist
                    shoulder_mid_y = (
                        person[LEFT_SHOULDER].y + person[RIGHT_SHOULDER].y
                    ) / 2
                    best_neck_y = (person[NOSE].y + shoulder_mid_y) / 2

        return best_neck_y if best_dist <= match_threshold else None

    def close(self) -> None:
        self._landmarker.close()
