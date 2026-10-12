"""Tests for RSI strategy."""

import pandas as pd
import pytest

from open_alice.strategies.rsi import RsiStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series(range(100, 200), dtype=float)
    return pd.DataFrame({"Close": prices}, index=dates)


def test_rsi_columns(sample_data: pd.DataFrame) -> None:
    strat = RsiStrategy(period=14)
    result = strat.generate_signals(sample_data)
    assert "RSI" in result.columns
    assert "Signal" in result.columns
    assert "Position" in result.columns


def test_rsi_bounds(sample_data: pd.DataFrame) -> None:
    strat = RsiStrategy(period=14)
    result = strat.generate_signals(sample_data)
    assert result["RSI"].dropna().between(0, 100).all()
