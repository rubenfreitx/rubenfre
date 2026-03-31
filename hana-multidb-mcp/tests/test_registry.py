import pytest
from unittest.mock import MagicMock

from src.registry import ConnectionRegistry


def _profile(alias: str = "db1", db_type: str = "hana") -> dict:
    return {
        "alias": alias,
        "db_type": db_type,
        "connection": {
            "host": "localhost",
            "port": 30015,
            "user": "user",
            "password": "pass",
        },
        "limits": {"query_timeout_sec": 10},
    }


# ── Profile management ────────────────────────────────────────────────────────

def test_set_profiles_stores_aliases():
    reg = ConnectionRegistry()
    reg.set_profiles({"db1": _profile("db1"), "db2": _profile("db2")})
    assert "db1" in reg._profiles
    assert "db2" in reg._profiles


def test_set_profiles_removes_old_open_connections():
    reg = ConnectionRegistry()
    mock_driver = MagicMock()
    reg._profiles["old"] = _profile("old")
    reg._connections["old"] = mock_driver

    reg.set_profiles({"new": _profile("new")})

    mock_driver.close.assert_called_once()
    assert "old" not in reg._connections
    assert "new" in reg._profiles


def test_set_profiles_keeps_existing_open_connections():
    reg = ConnectionRegistry()
    mock_driver = MagicMock()
    reg._profiles["db1"] = _profile("db1")
    reg._connections["db1"] = mock_driver

    # re-set with same aliases → connection should NOT be closed
    reg.set_profiles({"db1": _profile("db1"), "db2": _profile("db2")})

    mock_driver.close.assert_not_called()
    assert "db1" in reg._connections


# ── Connection access ─────────────────────────────────────────────────────────

def test_unknown_alias_raises_key_error():
    reg = ConnectionRegistry()
    with pytest.raises(KeyError, match="Unknown connection alias"):
        reg.get_or_connect("nonexistent")


def test_get_or_connect_returns_cached_driver():
    reg = ConnectionRegistry()
    mock_driver = MagicMock()
    reg._profiles["db1"] = _profile("db1")
    reg._connections["db1"] = mock_driver

    result = reg.get_or_connect("db1")

    assert result is mock_driver
    mock_driver.connect.assert_not_called()  # should NOT reconnect


def test_get_or_connect_creates_new_driver(monkeypatch):
    reg = ConnectionRegistry()
    reg._profiles["db1"] = _profile("db1")

    mock_driver = MagicMock()
    monkeypatch.setattr(
        "src.registry.ConnectionRegistry._create_driver",
        lambda self, p: mock_driver,
    )

    result = reg.get_or_connect("db1")

    assert result is mock_driver
    mock_driver.connect.assert_called_once_with(_profile("db1"))
    assert reg._connections["db1"] is mock_driver


# ── Teardown ──────────────────────────────────────────────────────────────────

def test_close_removes_connection_and_calls_driver():
    reg = ConnectionRegistry()
    mock_driver = MagicMock()
    reg._profiles["db1"] = _profile("db1")
    reg._connections["db1"] = mock_driver

    reg.close("db1")

    mock_driver.close.assert_called_once()
    assert "db1" not in reg._connections


def test_close_unknown_alias_is_noop():
    reg = ConnectionRegistry()
    reg.close("nonexistent")  # should not raise


def test_close_all():
    reg = ConnectionRegistry()
    m1, m2 = MagicMock(), MagicMock()
    reg._connections["a"] = m1
    reg._connections["b"] = m2

    reg.close_all()

    m1.close.assert_called_once()
    m2.close.assert_called_once()
    assert len(reg._connections) == 0


# ── Driver factory ────────────────────────────────────────────────────────────

def test_create_driver_hana():
    from src.drivers.hana import HanaDriver
    reg = ConnectionRegistry()
    driver = reg._create_driver(_profile(db_type="hana"))
    assert isinstance(driver, HanaDriver)


def test_create_driver_unsupported():
    reg = ConnectionRegistry()
    with pytest.raises(ValueError, match="Unsupported db_type"):
        reg._create_driver(_profile(db_type="postgres"))


# ── Reconnect ─────────────────────────────────────────────────────────────────

def test_reconnect_closes_and_reopens(monkeypatch):
    reg = ConnectionRegistry()
    reg._profiles["db1"] = _profile("db1")

    old_driver = MagicMock()
    reg._connections["db1"] = old_driver

    new_driver = MagicMock()
    monkeypatch.setattr(
        "src.registry.ConnectionRegistry._create_driver",
        lambda self, p: new_driver,
    )

    result = reg.reconnect("db1")

    old_driver.close.assert_called_once()
    new_driver.connect.assert_called_once()
    assert result is new_driver
