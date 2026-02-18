from commands.fallback import FallbackCommand


def test_execute_does_not_raise():
    cmd = FallbackCommand("fingers_extended:index")
    cmd.execute()


def test_name_attribute():
    cmd = FallbackCommand("some_gesture")
    assert cmd.name == "fallback"
