"""Tests for dashboard chart payloads (no Flask/MT5 required)."""

import pandas as pd
import pytest

from open_alice.dashboard.charts import build_strategy, chart_payload
from open_alice.data import add_returns


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=120, freq="D")
    prices = pd.Series([100.0] * 60 + [200.0] * 60, index=dates)
    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 1,
            "Low": prices - 1,
            "Close": prices,
            "Volume": 1000,
        }
    )
    return add_returns(df)


def test_build_strategy_names() -> None:
    for name in ("sma_crossover", "rsi", "macd", "bollinger"):
        assert build_strategy(name) is not None


def test_chart_payload_sma(sample_ohlcv: pd.DataFrame) -> None:
    payload = chart_payload(sample_ohlcv, "sma_crossover", fast=5, slow=10)
    assert len(payload["labels"]) == len(payload["close"])
    assert "SMA_fast" in payload["overlays"]
    assert "SMA_slow" in payload["overlays"]
    assert payload["metrics"]["num_trades"] >= 0
    assert len(payload["equity"]["values"]) == len(payload["labels"])


def test_chart_payload_all_strategies(sample_ohlcv: pd.DataFrame) -> None:
    for name in ("sma_crossover", "rsi", "macd", "bollinger"):
        payload = chart_payload(sample_ohlcv, name)
        assert payload["labels"]
        assert payload["metrics"]["win_rate"] >= 0
        assert isinstance(payload["markers"], list)


def test_chart_payload_downsamples(sample_ohlcv: pd.DataFrame) -> None:
    payload = chart_payload(sample_ohlcv, "rsi", max_points=20)
    assert len(payload["labels"]) <= 20


def test_demo_mode_blocks_live_order() -> None:
    import os

    os.environ["ALICE_DEMO"] = "1"
    try:
        from open_alice.dashboard.app import create_dashboard_app

        app = create_dashboard_app()
        client = app.test_client()
        resp = client.post(
            "/api/order",
            json={"symbol": "EURUSD", "side": "buy", "volume": 0.01, "live": True},
        )
        assert resp.status_code == 403
        assert "Demo mode" in resp.get_json()["message"]
    finally:
        del os.environ["ALICE_DEMO"]


def test_dry_run_order_still_works_in_demo_mode() -> None:
    import os

    os.environ["ALICE_DEMO"] = "1"
    try:
        from open_alice.dashboard.app import create_dashboard_app

        app = create_dashboard_app()
        client = app.test_client()
        resp = client.post(
            "/api/order",
            json={"symbol": "EURUSD", "side": "buy", "volume": 0.01},
        )
        assert resp.status_code == 200
        assert "DRY RUN" in resp.get_json()["message"]
    finally:
        del os.environ["ALICE_DEMO"]
