"""Market data fetching and caching."""

from __future__ import annotations

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
    return df


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add a simple daily returns column."""
    result = df.copy()
    result["Return"] = result["Close"].pct_change()
    return result
