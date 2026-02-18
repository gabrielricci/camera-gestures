from gestures.wake_gesture import is_wake_gesture


def test_closed_fist_is_wake_gesture():
    assert is_wake_gesture("closed_fist") is True


def test_fingers_extended_is_not_wake_gesture():
    assert is_wake_gesture("fingers_extended:index") is False


def test_no_hand_is_not_wake_gesture():
    assert is_wake_gesture("no_hand") is False


def test_none_is_not_wake_gesture():
    assert is_wake_gesture(None) is False


def test_arbitrary_string_is_not_wake_gesture():
    assert is_wake_gesture("open_palm") is False
