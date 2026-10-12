"""Tests for paper trading engine."""

import pandas as pd
import pytest

from open_alice.engine.paper import PaperPortfolio, run_paper
from open_alice.strategies.sma_crossover import SmaCrossover


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = pd.Series(range(100, 200), dtype=float)
    returns = prices.pct_change()
    return pd.DataFrame(
        {"Close": prices, "Return": returns, "Signal": 1, "Position": 1},
        index=dates,
    )


def test_paper_portfolio_buy_sell() -> None:
    portfolio = PaperPortfolio(cash=100_000)
    portfolio.buy("TEST", 100.0, 10)
    assert portfolio.cash == 99_000
    assert "TEST" in portfolio.positions

    portfolio.sell("TEST", 110.0)
    assert portfolio.cash == 100_100
    assert "TEST" not in portfolio.positions


def test_paper_portfolio_insufficient_funds() -> None:
    portfolio = PaperPortfolio(cash=100)
    portfolio.buy("TEST", 100.0, 10)
    assert portfolio.cash == 100
    assert "TEST" not in portfolio.positions


def test_run_paper(sample_ohlcv: pd.DataFrame) -> None:
    strategy = SmaCrossover(fast=5, slow=10)
    portfolio = run_paper(sample_ohlcv, strategy, "AAPL", initial_capital=100_000)
    assert portfolio.equity > 0
    assert isinstance(portfolio.trades, list)
