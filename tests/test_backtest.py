"""Tests for the backtesting engine."""

import pandas as pd
import pytest

from open_alice.engine.backtest import run_backtest


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series(range(100, 200), dtype=float)
    returns = prices.pct_change()
    return pd.DataFrame(
        {
            "Close": prices,
            "Return": returns,
            "Signal": [1] * 50 + [-1] * 50,
            "Position": [1] * 50 + [-1] * 50,
        },
        index=dates,
    )


def test_backtest_returns_result(sample_ohlcv: pd.DataFrame) -> None:
    result = run_backtest(sample_ohlcv)
    assert result.total_return is not None
    assert result.sharpe_ratio is not None
    assert result.max_drawdown is not None
    assert result.num_trades is not None
    assert result.win_rate is not None


def test_backtest_equity_curve(sample_ohlcv: pd.DataFrame) -> None:
    result = run_backtest(sample_ohlcv, initial_capital=100_000)
    assert len(result.equity_curve) == 100
    assert result.equity_curve.iloc[0] == pytest.approx(100_000)
