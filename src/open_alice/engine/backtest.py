"""Backtesting engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestResult:
    """Results from a backtest run."""

    equity_curve: pd.Series
    returns: pd.Series
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    win_rate: float


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
) -> BacktestResult:
    """Run a simple backtest on a DataFrame with Signal and Position columns.

    Args:
        df: DataFrame with Close, Signal, and Position columns.
        initial_capital: Starting capital.
        commission: Per-trade commission as a fraction (0.001 = 0.1%).

    Returns:
        BacktestResult with performance metrics.
    """
    out = df.copy()

    # Strategy returns: position * daily return
    out["Strategy_Return"] = out["Position"].shift(1).fillna(0) * out["Return"]

    # Apply commission on position changes
    out["Position_Change"] = out["Position"].diff().abs().fillna(0)
    out["Strategy_Return"] = out["Strategy_Return"] - out["Position_Change"] * commission

    # Equity curve
    out["Equity"] = initial_capital * (1 + out["Strategy_Return"].fillna(0)).cumprod()

    equity = out["Equity"]
    returns = out["Strategy_Return"].fillna(0)

    # Metrics
    total_return = float(equity.iloc[-1] / initial_capital - 1)

    # Sharpe ratio (annualized, assuming 252 trading days)
    mean_return = returns.mean()
    std_return = returns.std()
    sharpe = float((mean_return / std_return) * (252**0.5)) if std_return > 0 else 0.0

    # Max drawdown
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())

    # Trade count and win rate
    num_trades = int((out["Position_Change"] > 0).sum())
    winning_trades = int((returns > 0).sum())
    total_trades_with_return = int((returns != 0).sum())
    win_rate = winning_trades / total_trades_with_return if total_trades_with_return > 0 else 0.0

    return BacktestResult(
        equity_curve=equity,
        returns=returns,
        total_return=total_return,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        num_trades=num_trades,
        win_rate=win_rate,
    )
