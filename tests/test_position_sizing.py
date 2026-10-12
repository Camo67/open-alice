"""Tests for position sizing and risk management."""

import pytest

from open_alice.risk.position_sizing import PositionSizer


def test_calculate_size_basic() -> None:
    sizer = PositionSizer(risk_per_trade=0.02)
    # $100k capital, risk 2% = $2000, risk $5/share => 400 shares
    size = sizer.calculate_size(capital=100_000, entry_price=100, stop_price=95)
    assert size == 400


def test_calculate_size_zero_risk_per_share() -> None:
    sizer = PositionSizer(risk_per_trade=0.02)
    size = sizer.calculate_size(capital=100_000, entry_price=100, stop_price=100)
    assert size == 0


def test_should_exit_stop_loss() -> None:
    sizer = PositionSizer(stop_loss_pct=0.05)
    # Long position, price dropped 6% — should exit
    assert sizer.should_exit(entry_price=100, current_price=94, position=1) is True


def test_should_exit_take_profit() -> None:
    sizer = PositionSizer(take_profit_pct=0.10)
    # Long position, price rose 12% — should exit
    assert sizer.should_exit(entry_price=100, current_price=112, position=1) is True


def test_should_not_exit() -> None:
    sizer = PositionSizer(stop_loss_pct=0.05, take_profit_pct=0.10)
    # Long position, price moved 2% — within bounds
    assert sizer.should_exit(entry_price=100, current_price=102, position=1) is False


def test_invalid_risk_per_trade() -> None:
    with pytest.raises(ValueError):
        PositionSizer(risk_per_trade=1.5)
