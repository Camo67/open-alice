"""Tests for market data cleaning."""

import numpy as np
import pandas as pd

from open_alice.data import clean_ohlcv


def test_clean_ohlcv_drops_nan_and_inf_rows() -> None:
    df = pd.DataFrame(
        {
            "Open": [1.0, np.nan, 3.0, 4.0],
            "High": [1.0, 2.0, 3.0, 4.0],
            "Low": [1.0, 2.0, np.inf, 4.0],
            "Close": [1.0, 2.0, 3.0, np.nan],
        }
    )
    clean = clean_ohlcv(df)
    assert len(clean) == 1
    assert np.isfinite(clean[["Open", "High", "Low", "Close"]].to_numpy()).all()


def test_clean_ohlcv_passthrough_without_ohlc_columns() -> None:
    df = pd.DataFrame({"Other": [1.0, np.nan]})
    assert len(clean_ohlcv(df)) == 2
