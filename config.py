"""Load config.yaml and expose values as module-level attributes."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

_FILE = Path(os.path.dirname(__file__)) / "config.yaml"

with open(_FILE) as _f:
    _data: dict = yaml.safe_load(_f)

CAMERA_INDEX: int = _data["camera_index"]
FRAME_WIDTH: int = _data["frame_width"]
FRAME_HEIGHT: int = _data["frame_height"]

WAKE_HOLD_SECONDS: float = _data["wake_hold_seconds"]
COMMAND_HOLD_SECONDS: float = _data["command_hold_seconds"]
COMMAND_TIMEOUT_SECONDS: float = _data["command_timeout_seconds"]
COMMAND_DEBOUNCE_SECONDS: float = _data["command_debounce_seconds"]

GUI_ENABLED: bool = _data["gui_enabled"]

MEDIAPIPE_MAX_HANDS: int = _data["mediapipe_max_hands"]
MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = _data["mediapipe_min_detection_confidence"]
MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = _data["mediapipe_min_tracking_confidence"]

POSE_WRIST_MATCH_THRESHOLD: float = _data.get("pose_wrist_match_threshold", 0.15)
