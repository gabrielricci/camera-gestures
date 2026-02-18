"""Reset global state between every test."""

import pytest

import bus
import context
import integrations as _integrations


@pytest.fixture(autouse=True)
def reset_globals():
    bus._listeners.clear()
    context._services.clear()
    _integrations._cache = None
    yield
    bus._listeners.clear()
    context._services.clear()
    _integrations._cache = None
