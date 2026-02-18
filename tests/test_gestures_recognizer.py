"""Tests for gesture recognition logic.

Landmark indices used by the recognizer:
  0=WRIST, 1=THUMB_CMC, 2=THUMB_MCP, 3=THUMB_IP, 4=THUMB_TIP
  5=INDEX_MCP, 6=INDEX_PIP, 8=INDEX_TIP
  9=MIDDLE_MCP, 10=MIDDLE_PIP, 12=MIDDLE_TIP
  14=RING_PIP, 16=RING_TIP
  18=PINKY_PIP, 20=PINKY_TIP

_fist_points_up: y-distance(INDEX_MCP→INDEX_TIP) > x-distance → hand vertical
_finger_is_extended: tip.y < pip.y  (smaller y = higher on screen)
_thumb_is_extended: all x-deltas from wrist→tip share the same sign
"""

from gestures.recognizer import recognize


class LM:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y


def _make(overrides: dict) -> list:
    """Return 21 zero-initialised landmarks with selective overrides."""
    lm = [LM() for _ in range(21)]
    for idx, (x, y) in overrides.items():
        lm[idx].x = x
        lm[idx].y = y
    return lm


# ---------------------------------------------------------------------------
# Helpers to build common configurations
# ---------------------------------------------------------------------------

def _pointing_up_base():
    """Index MCP above index TIP (y-distance dominates) so fist_points_up=True.
    All non-thumb fingers folded (tip.y > pip.y).
    Thumb not extended (alternating x-deltas).
    """
    return {
        # index MCP (5) higher than index TIP (8) on screen → y-gap big, x-gap zero
        5: (0.5, 0.4),   # INDEX_MCP
        8: (0.5, 0.8),   # INDEX_TIP   — below MCP, not extended
        6: (0.5, 0.6),   # INDEX_PIP
        # middle folded
        12: (0.5, 0.8),  # MIDDLE_TIP
        10: (0.5, 0.6),  # MIDDLE_PIP
        # ring folded
        16: (0.5, 0.8),  # RING_TIP
        14: (0.5, 0.6),  # RING_PIP
        # pinky folded
        20: (0.5, 0.8),  # PINKY_TIP
        18: (0.5, 0.6),  # PINKY_PIP
        # thumb not extended: alternating sign on x-deltas
        0: (0.5, 0.5),   # WRIST
        1: (0.6, 0.5),   # THUMB_CMC
        2: (0.5, 0.5),   # THUMB_MCP
        3: (0.6, 0.5),   # THUMB_IP
        4: (0.5, 0.5),   # THUMB_TIP
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_landmarks_returns_no_hand():
    assert recognize(None) == "no_hand"


def test_empty_landmarks_returns_no_hand():
    assert recognize([]) == "no_hand"


def test_hand_not_pointing_up_returns_no_hand():
    # Make x-distance dominate → hand horizontal
    lm = _make({
        5: (0.2, 0.5),  # INDEX_MCP
        8: (0.8, 0.5),  # INDEX_TIP  — same y, large x gap
    })
    assert recognize(lm) == "no_hand"


def test_closed_fist_pointing_up():
    lm = _make(_pointing_up_base())
    assert recognize(lm) == "closed_fist"


def test_index_finger_extended():
    overrides = _pointing_up_base()
    overrides[8] = (0.5, 0.2)  # INDEX_TIP above INDEX_PIP → extended
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:index"


def test_middle_finger_extended():
    overrides = _pointing_up_base()
    overrides[12] = (0.5, 0.2)  # MIDDLE_TIP above MIDDLE_PIP
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:middle"


def test_ring_finger_extended():
    overrides = _pointing_up_base()
    overrides[16] = (0.5, 0.2)  # RING_TIP above RING_PIP
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:ring"


def test_pinky_extended():
    overrides = _pointing_up_base()
    overrides[20] = (0.5, 0.2)  # PINKY_TIP above PINKY_PIP
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:pinky"


def test_index_and_middle_extended():
    overrides = _pointing_up_base()
    overrides[8] = (0.5, 0.2)
    overrides[12] = (0.5, 0.2)
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:index+middle"


def test_thumb_extended_right():
    overrides = _pointing_up_base()
    # All x-values increase wrist→tip → thumb extended to the right
    overrides[0] = (0.3, 0.5)   # WRIST
    overrides[1] = (0.4, 0.5)   # THUMB_CMC
    overrides[2] = (0.5, 0.5)   # THUMB_MCP
    overrides[3] = (0.6, 0.5)   # THUMB_IP
    overrides[4] = (0.7, 0.5)   # THUMB_TIP
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:thumb"


def test_thumb_extended_left():
    overrides = _pointing_up_base()
    # All x-values decrease wrist→tip → thumb extended to the left
    overrides[0] = (0.7, 0.5)
    overrides[1] = (0.6, 0.5)
    overrides[2] = (0.5, 0.5)
    overrides[3] = (0.4, 0.5)
    overrides[4] = (0.3, 0.5)
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:thumb"


def test_thumb_and_pinky_extended():
    overrides = _pointing_up_base()
    overrides[0] = (0.3, 0.5)
    overrides[1] = (0.4, 0.5)
    overrides[2] = (0.5, 0.5)
    overrides[3] = (0.6, 0.5)
    overrides[4] = (0.7, 0.5)
    overrides[20] = (0.5, 0.2)
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:thumb+pinky"


def test_all_fingers_extended():
    overrides = _pointing_up_base()
    overrides[0] = (0.3, 0.5)
    overrides[1] = (0.4, 0.5)
    overrides[2] = (0.5, 0.5)
    overrides[3] = (0.6, 0.5)
    overrides[4] = (0.7, 0.5)
    overrides[8] = (0.5, 0.2)
    overrides[12] = (0.5, 0.2)
    overrides[16] = (0.5, 0.2)
    overrides[20] = (0.5, 0.2)
    lm = _make(overrides)
    assert recognize(lm) == "fingers_extended:thumb+index+middle+ring+pinky"
