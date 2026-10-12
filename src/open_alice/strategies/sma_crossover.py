"""Simple Moving Average Crossover strategy."""

from __future__ import annotations

import pandas as pd


class SmaCrossover:
    """Generate buy/sell signals based on SMA crossover.

    Buy when the fast SMA crosses above the slow SMA.
    Sell when the fast SMA crosses below the slow SMA.
    """

    def __init__(self, fast: int = 20, slow: int = 50) -> None:
        if fast >= slow:
            raise ValueError("fast period must be less than slow period")
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add signal columns to the DataFrame.

        Returns:
            DataFrame with added columns:
                SMA_fast, SMA_slow, Signal (1=buy, -1=sell, 0=hold), Position.
        """
        out = df.copy()
        out["SMA_fast"] = out["Close"].rolling(self.fast).mean()
        out["SMA_slow"] = out["Close"].rolling(self.slow).mean()

        out["Signal"] = 0
        out.loc[out["SMA_fast"] > out["SMA_slow"], "Signal"] = 1
        out.loc[out["SMA_fast"] < out["SMA_slow"], "Signal"] = -1

        # Position: forward-fill the signal (stay in position until signal changes)
        out["Position"] = out["Signal"].replace(0, pd.NA).ffill().fillna(0).astype(int)

        return out
