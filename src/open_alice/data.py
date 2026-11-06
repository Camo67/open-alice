"""Market data fetching and caching."""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


def fetch_ohlcv(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch OHLCV data for a symbol via yfinance.

    Args:
        symbol: Ticker symbol (e.g. "AAPL", "BTC-USD").
        period: Data period ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max").
        interval: Bar interval ("1m", "5m", "15m", "1h", "1d", "1wk", "1mo").

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume.
    """
    ticker = yf.Ticker(symbol)
    raw = ticker.history(period=period, interval=interval, auto_adjust=True)
    if raw.empty:
        raise ValueError(f"No data returned for symbol: {symbol}")
    df = pd.DataFrame(raw)
    df.index = pd.DatetimeIndex(df.index).tz_localize(None)
    df = clean_ohlcv(df)
    if df.empty:
        raise ValueError(f"No valid price rows for symbol: {symbol}")
    return df


def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing or non-finite OHLC values.

    Providers sometimes return bars with no valid price (for example an
    incomplete current session). Those rows must never reach the engines,
    or trades get recorded at NaN prices.
    """
    cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
    if not cols:
        return df
    values = df[cols].to_numpy(dtype=float, na_value=np.nan)
    finite_mask = np.isfinite(values).all(axis=1)
    result: pd.DataFrame = df[finite_mask]
    return result


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add a simple daily returns column."""
    result = df.copy()
    result["Return"] = result["Close"].pct_change()
    return result
