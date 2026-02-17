from typing import Optional

"""Recognize command gestures from hand landmarks."""

# MediaPipe hand landmark indices.
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_FINGER_MCP = 5
INDEX_FINGER_PIP = 6
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_PIP = 10
MIDDLE_FINGER_TIP = 12
RING_FINGER_PIP = 14
RING_FINGER_TIP = 16
MIDDLE_FINGER_MCP = 9
PINKY_PIP = 18
PINKY_TIP = 20


def _fist_points_up(lm) -> bool:
    """True when the wrist is pointing up"""
    index_distance_x = abs((lm[INDEX_FINGER_MCP].x - lm[INDEX_FINGER_TIP].x) * -1)
    index_distance_y = abs((lm[INDEX_FINGER_MCP].y - lm[INDEX_FINGER_TIP].y) * -1)

    return index_distance_y > index_distance_x


def _finger_is_extended(lm, tip, pip) -> bool:
    """
    Simple logic: is tip higher than joint
    """
    return lm[tip].y < lm[pip].y


def _thumb_is_extended(lm) -> bool:
    """
    For the thumb, if checks whether or not the distance between the thumb points and wrist base all points to the same direction (no curvature on the X axis)
    """
    distances = [
        lm[THUMB_TIP].x - lm[THUMB_IP].x,
        lm[THUMB_IP].x - lm[THUMB_MCP].x,
        lm[THUMB_MCP].x - lm[THUMB_CMC].x,
        lm[THUMB_CMC].x - lm[WRIST].x,
    ]

    return all(x > 0 for x in distances) or all(x < 0 for x in distances)


def recognize(landmarks: Optional[list]) -> str | None:
    """
    Return a gesture name string, or None if unrecognized.
    """
    if not landmarks or not _fist_points_up(landmarks):
        return "no_hand"

    lm = landmarks

    index_extended = _finger_is_extended(lm, INDEX_FINGER_TIP, INDEX_FINGER_PIP)
    middle_extended = _finger_is_extended(lm, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP)
    ring_extended = _finger_is_extended(lm, RING_FINGER_TIP, RING_FINGER_PIP)
    pinky_extended = _finger_is_extended(lm, PINKY_TIP, PINKY_PIP)
    thumb_extended = _thumb_is_extended(lm)

    if (
        not index_extended
        and not middle_extended
        and not ring_extended
        and not pinky_extended
        and not thumb_extended
        and _fist_points_up(lm)
    ):
        return "closed_fist"

    # Build a description for any other detected posture.
    names = []
    if thumb_extended:
        names.append("thumb")
    if index_extended:
        names.append("index")
    if middle_extended:
        names.append("middle")
    if ring_extended:
        names.append("ring")
    if pinky_extended:
        names.append("pinky")

    if names:
        return "fingers_extended:" + "+".join(names)

    return None
