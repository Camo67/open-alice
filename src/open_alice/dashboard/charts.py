"""Pure helpers that turn strategy output into dashboard JSON payloads."""

from __future__ import annotations

from typing import Any

import pandas as pd

from open_alice.engine import run_backtest
from open_alice.strategies import (
    BollingerStrategy,
    MacdStrategy,
    RsiStrategy,
    SmaCrossover,
    Strategy,
)

_OVERLAY_COLUMNS: dict[str, list[str]] = {
    "sma_crossover": ["SMA_fast", "SMA_slow"],
    "rsi": ["RSI"],
    "macd": ["MACD", "MACD_Signal"],
    "bollinger": ["BB_Upper", "BB_Mid", "BB_Lower"],
}


def build_strategy(name: str, fast: int = 20, slow: int = 50) -> Strategy:
    """Build a strategy instance by name."""
    if name == "sma_crossover":
        return SmaCrossover(fast=fast, slow=slow)
    factories: dict[str, type[Strategy]] = {
        "rsi": RsiStrategy,
        "macd": MacdStrategy,
        "bollinger": BollingerStrategy,
    }
    return factories[name]()


def chart_payload(
    df: pd.DataFrame,
    strategy_name: str,
    fast: int = 20,
    slow: int = 50,
    max_points: int = 300,
) -> dict[str, Any]:
    """Run a strategy + backtest and return a JSON-serializable chart payload.

    Args:
        df: OHLCV DataFrame with a Returns column (see data.add_returns).
        strategy_name: One of sma_crossover, rsi, macd, bollinger.
        fast: Fast SMA period (sma_crossover only).
        slow: Slow SMA period (sma_crossover only).
        max_points: Downsample to at most this many chart points.

    Returns:
        Dict with labels, close, overlays, markers, equity and metrics.
    """
    strategy = build_strategy(strategy_name, fast=fast, slow=slow)
    framed = strategy.generate_signals(df)
    if len(framed) > max_points:
        step = len(framed) // max_points + 1
        framed = framed.iloc[::step]

    result = run_backtest(framed)

    labels = [_label(ts) for ts in framed.index]
    payload: dict[str, Any] = {
        "labels": labels,
        "close": [float(v) for v in framed["Close"].tolist()],
        "overlays": {
            col: [None if pd.isna(v) else float(v) for v in framed[col].tolist()]
            for col in _OVERLAY_COLUMNS[strategy_name]
            if col in framed.columns
        },
        "markers": _signal_markers(framed),
        "equity": {
            "labels": labels,
            "values": [float(v) for v in result.equity_curve.tolist()],
        },
        "metrics": {
            "total_return": result.total_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "num_trades": result.num_trades,
            "win_rate": result.win_rate,
        },
    }
    return payload


def _label(ts: Any) -> str:
    if hasattr(ts, "isoformat"):
        return str(ts.isoformat())
    return str(ts)


def _signal_markers(framed: pd.DataFrame) -> list[dict[str, Any]]:
    """Extract fresh buy/sell markers from Signal/Position columns."""
    if "Signal" not in framed.columns:
        return []
    sig = framed["Signal"]
    prev = sig.shift(1).fillna(0)
    markers: list[dict[str, Any]] = []
    for ts, row in framed[(sig == 1) & (prev != 1)].iterrows():
        markers.append({"t": _label(ts), "price": float(row["Close"]), "side": "buy"})
    for ts, row in framed[(sig == -1) & (prev != -1)].iterrows():
        markers.append({"t": _label(ts), "price": float(row["Close"]), "side": "sell"})
    return markers
