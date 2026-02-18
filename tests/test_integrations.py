import pytest
import yaml
from pathlib import Path
from unittest.mock import patch

import integrations as _int


@pytest.fixture
def int_file(tmp_path, monkeypatch):
    """Point integrations._FILE at a temp path and reset cache."""
    path = tmp_path / "integrations.yaml"
    monkeypatch.setattr(_int, "_FILE", path)
    yield path


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

def test_load_creates_file_if_missing(int_file):
    assert not int_file.exists()
    result = _int.load()
    assert int_file.exists()
    assert result == {}


def test_load_reads_existing_file(int_file):
    int_file.write_text(yaml.dump({"hue": {"enabled": True}}))
    result = _int.load()
    assert result == {"hue": {"enabled": True}}


def test_load_caches_result(int_file):
    int_file.write_text(yaml.dump({"hue": {"enabled": True}}))
    first = _int.load()
    int_file.write_text(yaml.dump({"hue": {"enabled": False}}))
    second = _int.load()
    assert first is second  # same object from cache


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_returns_integration_config(int_file):
    int_file.write_text(yaml.dump({"hue": {"bridge_ip": "192.168.1.1"}}))
    assert _int.get("hue") == {"bridge_ip": "192.168.1.1"}


def test_get_missing_key_returns_default(int_file):
    int_file.write_text(yaml.dump({"hue": {}}))
    assert _int.get("tuya", {}) == {}


def test_get_missing_key_no_default_returns_empty_dict(int_file):
    int_file.write_text(yaml.dump({"hue": {}}))
    assert _int.get("nonexistent") == {}


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_merges_keys(int_file):
    int_file.write_text(yaml.dump({"hue": {"enabled": False, "bridge_ip": "0.0.0.0"}}))
    _int.load()
    _int.update("hue", enabled=True)
    data = yaml.safe_load(int_file.read_text())
    assert data["hue"]["enabled"] is True
    assert data["hue"]["bridge_ip"] == "0.0.0.0"


def test_update_creates_new_integration_section(int_file):
    int_file.write_text(yaml.dump({}))
    _int.load()
    _int.update("tuya", api_key="abc123", enabled=True)
    data = yaml.safe_load(int_file.read_text())
    assert data["tuya"]["api_key"] == "abc123"
    assert data["tuya"]["enabled"] is True


def test_update_persists_to_disk(int_file):
    int_file.write_text(yaml.dump({"hue": {}}))
    _int.load()
    _int.update("hue", bridge_ip="10.0.0.1")
    raw = yaml.safe_load(int_file.read_text())
    assert raw["hue"]["bridge_ip"] == "10.0.0.1"


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

def test_save_writes_cache_to_disk(int_file):
    int_file.write_text(yaml.dump({"hue": {"enabled": False}}))
    _int.load()
    _int._cache["hue"]["enabled"] = True
    _int.save()
    raw = yaml.safe_load(int_file.read_text())
    assert raw["hue"]["enabled"] is True
