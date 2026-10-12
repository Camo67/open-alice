"""Tests for Bollinger Bands strategy."""

import pandas as pd
import pytest

from open_alice.strategies.bollinger import BollingerStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series(range(100, 200), dtype=float)
    return pd.DataFrame({"Close": prices}, index=dates)


def test_bollinger_columns(sample_data: pd.DataFrame) -> None:
    strat = BollingerStrategy(period=20)
    result = strat.generate_signals(sample_data)
    assert "BB_Mid" in result.columns
    assert "BB_Upper" in result.columns
    assert "BB_Lower" in result.columns
    assert "Signal" in result.columns
    assert "Position" in result.columns


def test_bollinger_upper_above_lower(sample_data: pd.DataFrame) -> None:
    strat = BollingerStrategy(period=20)
    result = strat.generate_signals(sample_data)
    valid = result.dropna(subset=["BB_Upper", "BB_Lower"])
    assert (valid["BB_Upper"] >= valid["BB_Lower"]).all()
