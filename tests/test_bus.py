import bus


def test_emit_calls_registered_listener():
    received = []
    bus.on("test_event", lambda **kw: received.append(kw))
    bus.emit("test_event", value=42)
    assert received == [{"value": 42}]


def test_emit_calls_multiple_listeners():
    calls = []
    bus.on("evt", lambda **kw: calls.append("a"))
    bus.on("evt", lambda **kw: calls.append("b"))
    bus.emit("evt")
    assert calls == ["a", "b"]


def test_off_stops_listener():
    calls = []
    cb = lambda **kw: calls.append(1)
    bus.on("evt", cb)
    bus.off("evt", cb)
    bus.emit("evt")
    assert calls == []


def test_emit_unknown_event_does_not_raise():
    bus.emit("no_such_event", x=1)


def test_emit_passes_kwargs_to_listener():
    received = {}

    def cb(**kw):
        received.update(kw)

    bus.on("ev", cb)
    bus.emit("ev", a=1, b="hello")
    assert received == {"a": 1, "b": "hello"}


def test_listeners_are_independent_per_event():
    calls = []
    bus.on("event_a", lambda **kw: calls.append("a"))
    bus.emit("event_b")
    assert calls == []
