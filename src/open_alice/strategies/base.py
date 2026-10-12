"""Base strategy protocol."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class Strategy(Protocol):
    """Protocol that all trading strategies must implement."""

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from OHLCV data."""
        ...
