"""MACD (Moving Average Convergence Divergence) strategy."""

from __future__ import annotations

import pandas as pd


class MacdStrategy:
    """Buy when MACD line crosses above signal line, sell when it crosses below."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        ema_fast = out["Close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = out["Close"].ewm(span=self.slow, adjust=False).mean()

        out["MACD"] = ema_fast - ema_slow
        out["MACD_Signal"] = out["MACD"].ewm(span=self.signal, adjust=False).mean()
        out["MACD_Hist"] = out["MACD"] - out["MACD_Signal"]

        out["Signal"] = 0
        out.loc[out["MACD"] > out["MACD_Signal"], "Signal"] = 1
        out.loc[out["MACD"] < out["MACD_Signal"], "Signal"] = -1

        out["Position"] = out["Signal"].replace(0, pd.NA).ffill().fillna(0).astype(int)
        return out
