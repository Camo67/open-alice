"""Tests for SMA Crossover strategy."""

import pandas as pd
import pytest

from open_alice.strategies.sma_crossover import SmaCrossover


@pytest.fixture
def sample_data() -> pd.DataFrame:
    # Create data with a clear uptrend: first 50 days at 100, next 50 days at 200
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series([100.0] * 50 + [200.0] * 50, index=dates)
    return pd.DataFrame({"Close": prices}, index=dates)


def test_generate_signals_columns(sample_data: pd.DataFrame) -> None:
    strat = SmaCrossover(fast=5, slow=10)
    result = strat.generate_signals(sample_data)
    assert "SMA_fast" in result.columns
    assert "SMA_slow" in result.columns
    assert "Signal" in result.columns
    assert "Position" in result.columns


def test_invalid_periods() -> None:
    with pytest.raises(ValueError):
        SmaCrossover(fast=50, slow=20)


def test_uptrend_generates_buy_signal(sample_data: pd.DataFrame) -> None:
    strat = SmaCrossover(fast=5, slow=10)
    result = strat.generate_signals(sample_data)
    
    # After the trend is established, we should have a buy signal
    assert (result["Signal"] == 1).any()
    # We should never have a sell signal in this scenario
    assert (result["Signal"] == -1).sum() == 0
