"""Tests for SMA Crossover strategy."""

import pandas as pd
import pytest

from open_alice.strategies.sma_crossover import SmaCrossover


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series(range(100, 200), dtype=float)
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
    # In a strong uptrend, fast SMA should be above slow SMA
    assert result["Signal"].iloc[-1] == 1
