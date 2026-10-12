"""Position sizing and risk management."""

from __future__ import annotations


class PositionSizer:
    """Fixed-fractional position sizing.

    Risks a fixed fraction of capital per trade, with optional
    stop-loss and take-profit levels.
    """

    def __init__(
        self,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10,
    ) -> None:
        if not 0 < risk_per_trade <= 1:
            raise ValueError("risk_per_trade must be between 0 and 1")
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def calculate_size(self, capital: float, entry_price: float, stop_price: float) -> int:
        """Calculate position size based on risk.

        Args:
            capital: Current capital.
            entry_price: Entry price per share.
            stop_price: Stop-loss price per share.

        Returns:
            Number of shares to trade (integer, floored).
        """
        risk_amount = capital * self.risk_per_trade
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share == 0:
            return 0
        return int(risk_amount / risk_per_share)

    def should_exit(self, entry_price: float, current_price: float, position: int) -> bool:
        """Check if stop-loss or take-profit has been hit.

        Args:
            entry_price: Original entry price.
            current_price: Current market price.
            position: Current position (positive=long, negative=short).

        Returns:
            True if the position should be closed.
        """
        if position == 0:
            return False

        pnl_pct = (current_price - entry_price) / entry_price
        if position > 0:
            return pnl_pct <= -self.stop_loss_pct or pnl_pct >= self.take_profit_pct
        else:
            return pnl_pct >= self.stop_loss_pct or pnl_pct <= -self.take_profit_pct
