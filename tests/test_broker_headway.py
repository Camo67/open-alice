"""Tests for Headway presets and credential storage."""

from open_alice.broker.config import (
    clear_credentials,
    load_credentials,
    save_credentials,
)
from open_alice.broker.headway import list_headway_servers, resolve_headway_server


def test_list_headway_servers() -> None:
    servers = list_headway_servers()
    assert "Headway-Demo" in servers["demo"]
    assert "Headway-Real" in servers["real"]


def test_resolve_headway_server_defaults() -> None:
    assert resolve_headway_server(None, demo=True) == "Headway-Demo"
    assert resolve_headway_server(None, demo=False) == "Headway-Real"
    assert resolve_headway_server("demo") == "Headway-Demo"
    assert resolve_headway_server("real") == "Headway-Real"
    assert resolve_headway_server("Headway-Demo") == "Headway-Demo"


def test_save_and_load_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    save_credentials(12345678, "secret-pass", "Headway-Demo")
    loaded = load_credentials()
    assert loaded is not None
    assert loaded["login"] == "12345678"
    assert loaded["password"] == "secret-pass"
    assert loaded["server"] == "Headway-Demo"
    assert clear_credentials() is True
    assert load_credentials() is None
