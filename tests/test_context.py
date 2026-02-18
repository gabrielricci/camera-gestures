import pytest
import context


def test_register_and_get():
    service = object()
    context.register("my_service", service)
    assert context.get("my_service") is service


def test_register_overwrites_existing():
    context.register("svc", "first")
    context.register("svc", "second")
    assert context.get("svc") == "second"


def test_get_missing_key_raises():
    with pytest.raises(KeyError):
        context.get("does_not_exist")


def test_multiple_services_are_independent():
    context.register("a", 1)
    context.register("b", 2)
    assert context.get("a") == 1
    assert context.get("b") == 2
