"""Paper trading engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from open_alice.strategies.base import Strategy


@dataclass
class PaperPosition:
    symbol: str
    shares: int
    entry_price: float
    entry_time: datetime


@dataclass
class PaperPortfolio:
    cash: float
    positions: dict[str, PaperPosition] = field(default_factory=dict)
    trades: list[dict[str, object]] = field(default_factory=list)

    @property
    def equity(self) -> float:
        total = self.cash
        for pos in self.positions.values():
            total += pos.shares * pos.entry_price
        return total

    def buy(self, symbol: str, price: int, shares: int) -> None:
        cost = shares * price
        if cost > self.cash:
            return
        self.cash -= cost
        self.positions[symbol] = PaperPosition(symbol, shares, price, datetime.now())
        self.trades.append({
            "time": datetime.now(),
            "action": "BUY",
            "symbol": symbol,
            "shares": shares,
            "price": price,
        })

    def sell(self, symbol: str, price: float) -> None:
        if symbol not in self.positions:
            return
        pos = self.positions.pop(symbol)
        proceeds = pos.shares * price
        self.cash += proceeds
        pnl = proceeds - (pos.shares * pos.entry_price)
        self.trades.append({
            "time": datetime.now(),
            "action": "SELL",
            "symbol": symbol,
            "shares": pos.shares,
            "price": price,
            "pnl": pnl,
        })


def run_paper(
    df: pd.DataFrame,
    strategy: Strategy,
    symbol: str,
    initial_capital: float = 100_000.0,
    risk_per_trade: float = 0.02,
) -> PaperPortfolio:
    """Run a paper trading simulation.

    Args:
        df: OHLCV DataFrame.
        strategy: Strategy with generate_signals method.
        initial_capital: Starting cash.
        risk_per_trade: Fraction of equity risked per trade.

    Returns:
        PaperPortfolio with final state and trade log.
    """
    portfolio = PaperPortfolio(cash=initial_capital)
    signals = strategy.generate_signals(df)

    for i in range(1, len(signals)):
        row = signals.iloc[i]
        prev = signals.iloc[i - 1]

        if row["Signal"] == 1 and prev["Signal"] != 1:
            # Buy signal
            risk_amount = portfolio.equity * risk_per_trade
            stop_distance = row["Close"] * 0.05
            if stop_distance > 0:
                shares = int(risk_amount / stop_distance)
                if shares > 0:
                    portfolio.buy(symbol, row["Close"], shares)

        elif row["Signal"] == -1 and prev["Signal"] != -1:
            # Sell signal
            for symbol in list(portfolio.positions.keys()):
                portfolio.sell(symbol, row["Close"])

    # Close all positions at the end
    final_price = signals["Close"].iloc[-1]
    for symbol in list(portfolio.positions.keys()):
        portfolio.sell(symbol, final_price)

    return portfolio
