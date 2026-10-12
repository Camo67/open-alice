"""Tests for MACD strategy."""

import pandas as pd
import pytest

from open_alice.strategies.macd import MacdStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series(range(100, 200), dtype=float)
    return pd.DataFrame({"Close": prices}, index=dates)


def test_macd_columns(sample_data: pd.DataFrame) -> None:
    strat = MacdStrategy()
    result = strat.generate_signals(sample_data)
    assert "MACD" in result.columns
    assert "MACD_Signal" in result.columns
    assert "MACD_Hist" in result.columns
    assert "Signal" in result.columns
    assert "Position" in result.columns
