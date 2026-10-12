"""CLI interface for open-alice."""

from __future__ import annotations

import argparse
import sys

from open_alice.data import add_returns, fetch_ohlcv
from open_alice.engine import run_backtest, run_paper
from open_alice.strategies import BollingerStrategy, MacdStrategy, RsiStrategy, SmaCrossover

STRATEGIES = {
    "sma_crossover": SmaCrossover,
    "rsi": RsiStrategy,
    "macd": MacdStrategy,
    "bollinger": BollingerStrategy,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="alice",
        description="Alice — an open-source AI trading bot",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backtest command
    bt = subparsers.add_parser("backtest", help="Run a backtest")
    bt.add_argument("--symbol", default="AAPL", help="Ticker symbol")
    bt.add_argument("--strategy", default="sma_crossover", choices=STRATEGIES.keys())
    bt.add_argument("--period", default="1y", help="Data period")
    bt.add_argument("--capital", type=float, default=100_000, help="Initial capital")
    bt.add_argument("--fast", type=int, default=20, help="Fast SMA period")
    bt.add_argument("--slow", type=int, default=50, help="Slow SMA period")

    # Paper trading command
    paper = subparsers.add_parser("paper", help="Run paper trading simulation")
    paper.add_argument("--symbol", default="AAPL", help="Ticker symbol")
    paper.add_argument("--strategy", default="sma_crossover", choices=STRATEGIES.keys())
    paper.add_argument("--period", default="1y", help="Data period")
    paper.add_argument("--capital", type=float, default=100_000, help="Initial capital")
    paper.add_argument("--risk", type=float, default=0.02, help="Risk per trade")

    args = parser.parse_args()

    if args.command == "backtest":
        _run_backtest(args)
    elif args.command == "paper":
        _run_paper(args)


def _build_strategy(name: str, args: argparse.Namespace) -> object:
    if name == "sma_crossover":
        return SmaCrossover(fast=args.fast, slow=args.slow)
    return STRATEGIES[name]()


def _run_backtest(args: argparse.Namespace) -> None:
    print(f"\n{'='*60}")
    print(f"  Alice Backtest — {args.symbol}")
    print(f"  Strategy: {args.strategy} | Period: {args.period} | Capital: ${args.capital:,.0f}")
    print(f"{'='*60}\n")

    df = fetch_ohlcv(args.symbol, period=args.period)
    df = add_returns(df)

    strategy = _build_strategy(args.strategy, args)
    df = strategy.generate_signals(df)

    result = run_backtest(df, initial_capital=args.capital)

    print(f"  Total Return:    {result.total_return:>10.2%}")
    print(f"  Sharpe Ratio:    {result.sharpe_ratio:>10.2f}")
    print(f"  Max Drawdown:    {result.max_drawdown:>10.2%}")
    print(f"  Num Trades:      {result.num_trades:>10d}")
    print(f"  Win Rate:        {result.win_rate:>10.2%}")
    print(f"\n{'='*60}\n")


def _run_paper(args: argparse.Namespace) -> None:
    print(f"\n{'='*60}")
    print(f"  Alice Paper Trading — {args.symbol}")
    print(f"  Strategy: {args.strategy} | Period: {args.period} | Capital: ${args.capital:,.0f}")
    print(f"{'='*60}\n")

    df = fetch_ohlcv(args.symbol, period=args.period)
    df = add_returns(df)

    strategy = _build_strategy(args.strategy, args)
    portfolio = run_paper(df, strategy, initial_capital=args.capital, risk_per_trade=args.risk)

    print(f"  Final Equity:    ${portfolio.equity:>10,.2f}")
    print(f"  Cash Remaining:  ${portfolio.cash:>10,.2f}")
    print(f"  Total Trades:    {len(portfolio.trades):>10d}")

    if portfolio.trades:
        total_pnl = sum(t.get("pnl", 0) for t in portfolio.trades)
        print(f"  Total P&L:       ${total_pnl:>10,.2f}")

    print("\n  --- Trade Log ---")
    for t in portfolio.trades[:20]:
        pnl_str = f"  P&L: ${t['pnl']:,.2f}" if "pnl" in t else ""
        print(
            f"  {t['time'].strftime('%Y-%m-%d %H:%M')} | {t['action']:>4} | "
            f"{t.get('symbol', ''):>6} | {t.get('shares', 0):>6} @ "
            f"${t.get('price', 0):>8.2f}{pnl_str}"
        )

    if len(portfolio.trades) > 20:
        print(f"  ... and {len(portfolio.trades) - 20} more trades")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
