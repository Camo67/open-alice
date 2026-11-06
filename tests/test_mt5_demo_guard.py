"""Demo-only safety uses reported mode, never a server-name heuristic."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from open_alice.broker import mt5 as broker_module
from open_alice.broker.mt5 import MT5Broker


def terminal(monkeypatch, *, mode=0, login=123, server="Broker-Demo"):
    info = SimpleNamespace(
        trade_mode=mode,
        login=login,
        server=server,
        balance=1000,
        equity=1000,
        margin=0,
        margin_free=1000,
        margin_level=0,
        currency="USD",
        leverage=100,
        trade_allowed=True,
        trade_expert=True,
    )
    api = Mock()
    api.ACCOUNT_TRADE_MODE_DEMO = 0
    api.initialize.return_value = True
    api.account_info.return_value = info
    api.ORDER_TYPE_BUY = 0
    api.ORDER_TYPE_SELL = 1
    api.order_send.return_value = SimpleNamespace(retcode=10009, order=1)
    api.TRADE_RETCODE_DONE = 10009
    api.symbol_info.return_value = SimpleNamespace(_asdict=lambda: {})
    api.symbol_info_tick.return_value = SimpleNamespace(ask=1.1, bid=1.0)
    api.positions_get.return_value = [
        SimpleNamespace(
            symbol="EURUSD",
            volume=0.01,
            type=0,
        )
    ]
    monkeypatch.setattr(broker_module, "_load_mt5", lambda: api)
    return api, info


@pytest.mark.parametrize("mode", [1, 2, None, "0", False])
def test_connect_rejects_non_demo_or_unknown(monkeypatch, mode):
    api, _ = terminal(monkeypatch, mode=mode)
    broker = MT5Broker()
    with pytest.raises(RuntimeError, match="not verified demo"):
        broker.connect()
    assert not broker.connected
    api.shutdown.assert_called_once()
    api.order_send.assert_not_called()


@pytest.mark.parametrize("field,value", [("login", 456), ("server", "Other-Demo")])
def test_connect_rejects_requested_identity_mismatch(monkeypatch, field, value):
    api, info = terminal(monkeypatch)
    setattr(info, field, value)
    with pytest.raises(RuntimeError, match="does not match"):
        MT5Broker(login=123, server="Broker-Demo").connect()
    api.order_send.assert_not_called()


@pytest.mark.parametrize("action", ["buy", "sell", "close"])
@pytest.mark.parametrize("change", ["real", "unknown", "login", "server"])
def test_rechecks_before_every_send(monkeypatch, action, change):
    api, info = terminal(monkeypatch)
    broker = MT5Broker()
    assert broker.connect()
    if change == "real":
        info.trade_mode = 2
    elif change == "unknown":
        info.trade_mode = None
    elif change == "login":
        info.login = 456
    else:
        info.server = "Other-Demo"
    with pytest.raises(RuntimeError, match="Demo-only safety"):
        broker.close_position(1) if action == "close" else getattr(broker, action)("EURUSD", 0.01)
    api.order_send.assert_not_called()


@pytest.mark.parametrize("action", ["buy", "sell", "close"])
def test_verified_unchanged_demo_can_send(monkeypatch, action):
    api, _ = terminal(monkeypatch, server="Broker-Training")
    broker = MT5Broker(login=123, server="Broker-Training")
    assert broker.connect()
    assert (
        broker.close_position(1) if action == "close" else getattr(broker, action)("EURUSD", 0.01)
    )
    api.order_send.assert_called_once()


def test_missing_demo_constant_rejected(monkeypatch):
    api, _ = terminal(monkeypatch)
    del api.ACCOUNT_TRADE_MODE_DEMO
    with pytest.raises(RuntimeError, match="not verified demo"):
        MT5Broker().connect()
    api.order_send.assert_not_called()


def test_missing_account_info_rejected(monkeypatch):
    api, _ = terminal(monkeypatch)
    api.account_info.return_value = None
    with pytest.raises(RuntimeError, match="not verified demo"):
        MT5Broker().connect()
    api.order_send.assert_not_called()


def test_switch_during_order_preparation_is_rejected(monkeypatch):
    api, info = terminal(monkeypatch)
    broker = MT5Broker()
    assert broker.connect()

    def switched_tick(symbol):
        info.trade_mode = 2
        return SimpleNamespace(ask=1.1, bid=1.0)

    api.symbol_info_tick.side_effect = switched_tick
    with pytest.raises(RuntimeError, match="not verified demo"):
        broker.buy("EURUSD", 0.01)
    api.order_send.assert_not_called()
