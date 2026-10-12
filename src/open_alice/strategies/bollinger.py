"""Bollinger Bands mean-reversion strategy."""

from __future__ import annotations

import pandas as pd


class BollingerStrategy:
    """Buy at lower band, sell at upper band."""

    def __init__(self, period: int = 20, num_std: float = 2.0) -> None:
        self.period = period
        self.num_std = num_std

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        out["BB_Mid"] = out["Close"].rolling(self.period).mean()
        bb_std = out["Close"].rolling(self.period).std()
        out["BB_Upper"] = out["BB_Mid"] + self.num_std * bb_std
        out["BB_Lower"] = out["BB_Mid"] - self.num_std * bb_std

        out["Signal"] = 0
        out.loc[out["Close"] < out["BB_Lower"], "Signal"] = 1
        out.loc[out["Close"] > out["BB_Upper"], "Signal"] = -1

        out["Position"] = out["Signal"].replace(0, pd.NA).ffill().fillna(0).astype(int)
        return out
