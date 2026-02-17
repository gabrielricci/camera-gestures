"""Wake gesture: closed fist with wrist above the middle-finger knuckle.

This module is deliberately isolated so the wake gesture can be swapped
by changing a single file.  Implement any callable with the signature
``(landmarks: list[NormalizedLandmark]) -> bool`` and wire it into main.py.
"""


def is_wake_gesture(gesture) -> bool:
    """Return True when the hand shows a closed fist with the wrist above
    the middle-finger MCP (knuckle).

    "Above" means a smaller y value because MediaPipe uses a coordinate
    system where y=0 is the top of the frame.
    """
    if gesture == "closed_fist":
        return True

    return False
