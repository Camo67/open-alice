"""RSI (Relative Strength Index) mean-reversion strategy."""

from __future__ import annotations

import pandas as pd


class RsiStrategy:
    """Buy when RSI oversold, sell when RSI overbought."""

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70) -> None:
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    @staticmethod
    def _rsi(prices: pd.Series, period: int) -> pd.Series:
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["RSI"] = self._rsi(out["Close"], self.period)

        out["Signal"] = 0
        out.loc[out["RSI"] < self.oversold, "Signal"] = 1
        out.loc[out["RSI"] > self.overbought, "Signal"] = -1

        out["Position"] = out["Signal"].replace(0, pd.NA).ffill().fillna(0).astype(int)
        return out
