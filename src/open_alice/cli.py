"""CLI interface for open-alice."""

from __future__ import annotations

import argparse
import getpass
import sys

from open_alice.broker import (
    clear_credentials,
    get_credentials_path,
    list_headway_servers,
    load_credentials,
    resolve_headway_server,
    save_credentials,
)
from open_alice.broker.mt5 import MT5Broker
from open_alice.data import add_returns, fetch_ohlcv
from open_alice.engine import run_backtest, run_paper
from open_alice.signals.webhook import TradingViewSignalReceiver, create_webhook_app
from open_alice.strategies import (
    BollingerStrategy,
    MacdStrategy,
    RsiStrategy,
    SmaCrossover,
    Strategy,
)

STRATEGIES: dict[str, type[Strategy]] = {
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
    bt.add_argument("--use-mt5", action="store_true", help="Use MT5 for data")

    # Paper trading command
    paper = subparsers.add_parser("paper", help="Run paper trading simulation")
    paper.add_argument("--symbol", default="AAPL", help="Ticker symbol")
    paper.add_argument("--strategy", default="sma_crossover", choices=STRATEGIES.keys())
    paper.add_argument("--period", default="1y", help="Data period")
    paper.add_argument("--capital", type=float, default=100_000, help="Initial capital")
    paper.add_argument("--risk", type=float, default=0.02, help="Risk per trade")
    paper.add_argument("--use-mt5", action="store_true", help="Use MT5 for data")

    # Live trading command (Headway via MT5)
    live = subparsers.add_parser("live", help="Run live trading with MT5/Headway")
    live.add_argument("--symbol", default="EURUSD", help="Ticker symbol")
    live.add_argument("--strategy", default="sma_crossover", choices=STRATEGIES.keys())
    live.add_argument("--fast", type=int, default=20, help="Fast SMA period")
    live.add_argument("--slow", type=int, default=50, help="Slow SMA period")
    live.add_argument("--login", type=int, help="MT5 login (defaults to saved)")
    live.add_argument("--password", type=str, help="MT5 password (defaults to saved)")
    live.add_argument("--server", type=str, help="MT5 server (defaults to saved)")
    live.add_argument("--demo", action="store_true", help="Use Headway demo server")
    live.add_argument("--risk", type=float, default=0.02, help="Risk per trade")
    live.add_argument("--interval", type=int, default=60, help="Check interval (seconds)")
    live.add_argument("--execute", action="store_true", help="Actually place orders")
    live.add_argument("--yes", action="store_true", help="Skip the live-orders confirmation")

    # Broker account management (Headway via MT5)
    broker = subparsers.add_parser("broker", help="Manage MT5 / Headway login")
    broker_sub = broker.add_subparsers(dest="broker_command", required=True)

    b_login = broker_sub.add_parser("login", help="Save Headway MT5 credentials")
    b_login.add_argument("--login", type=int, help="MT5 account number")
    b_login.add_argument("--server", type=str, help="MT5 server or 'demo'/'real'")
    b_login.add_argument("--demo", action="store_true", help="Shortcut for Headway demo")
    b_login.add_argument("--terminal-path", type=str, help="Path to terminal64.exe")

    broker_sub.add_parser("status", help="Show saved login and test connection")
    broker_sub.add_parser("logout", help="Delete saved MT5 credentials")

    # Webhook server command
    webhook = subparsers.add_parser("serve", help="Start webhook server for signals")
    webhook.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    webhook.add_argument("--port", type=int, default=5000, help="Port to bind to")
    webhook.add_argument("--secret", type=str, help="Secret for request validation")

    # Dashboard command
    dash = subparsers.add_parser("dashboard", help="Start the web dashboard")
    dash.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dash.add_argument("--port", type=int, default=8080, help="Port to bind to")

    args = parser.parse_args()

    if args.command == "backtest":
        _run_backtest(args)
    elif args.command == "paper":
        _run_paper(args)
    elif args.command == "live":
        _run_live(args)
    elif args.command == "broker":
        _run_broker(args)
    elif args.command == "serve":
        _run_webhook(args)
    elif args.command == "dashboard":
        _run_dashboard(args)


def _build_strategy(name: str, args: argparse.Namespace) -> Strategy:
    if name == "sma_crossover":
        fast = int(getattr(args, "fast", 20))
        slow = int(getattr(args, "slow", 50))
        return SmaCrossover(fast=fast, slow=slow)
    factory = STRATEGIES[name]
    return factory()


def _mt5_login_from_args(args: argparse.Namespace) -> tuple[int | None, str | None, str | None]:
    """Resolve MT5 credentials from flags, then saved file, then env."""
    login = getattr(args, "login", None)
    password = getattr(args, "password", None)
    server = getattr(args, "server", None)
    if login is not None and password is not None and server is not None:
        return int(login), str(password), str(server)
    saved = load_credentials()
    if saved is not None:
        return int(saved["login"]), saved["password"], saved["server"]
    return None, None, None


def _run_backtest(args: argparse.Namespace) -> None:
    use_mt5 = bool(getattr(args, "use_mt5", False))
    print(f"\n{'='*60}")
    print(f"  Alice Backtest — {args.symbol}")
    print(f"  Strategy: {args.strategy} | Period: {args.period} | Capital: ${args.capital:,.0f}")
    print(f"  Data Source: {'MT5' if use_mt5 else 'Yahoo Finance'}")
    print(f"{'='*60}\n")

    if use_mt5:
        import datetime

        login, password, server = _mt5_login_from_args(args)
        broker = MT5Broker(login=login, password=password, server=server)
        try:
            if broker.connect():
                end_date = datetime.datetime.now()
                start_date = end_date - datetime.timedelta(days=365)
                df = broker.get_historical_data(args.symbol, "1D", start_date, end_date)
                broker.disconnect()
                if df.empty:
                    print("Warning: MT5 returned no data, falling back to Yahoo Finance")
                    df = fetch_ohlcv(args.symbol, period=args.period)
            else:
                print("Warning: MT5 connect failed, falling back to Yahoo Finance")
                df = fetch_ohlcv(args.symbol, period=args.period)
        except Exception as exc:
            print(f"Warning: MT5 error ({exc}), falling back to Yahoo Finance")
            df = fetch_ohlcv(args.symbol, period=args.period)
    else:
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
    use_mt5 = bool(getattr(args, "use_mt5", False))
    print(f"\n{'='*60}")
    print(f"  Alice Paper Trading — {args.symbol}")
    print(f"  Strategy: {args.strategy} | Period: {args.period} | Capital: ${args.capital:,.0f}")
    print(f"  Data Source: {'MT5' if use_mt5 else 'Yahoo Finance'}")
    print(f"{'='*60}\n")

    if use_mt5:
        login, password, server = _mt5_login_from_args(args)
        broker = MT5Broker(login=login, password=password, server=server)
        try:
            from typing import Any

            mt5: Any = __import__("MetaTrader5")
            if broker.connect():
                df = broker.get_rates(args.symbol, mt5.TIMEFRAME_D1, 100)
                broker.disconnect()
                if df.empty:
                    print("Warning: MT5 returned no data, falling back to Yahoo Finance")
                    df = fetch_ohlcv(args.symbol, period=args.period)
            else:
                print("Warning: MT5 connect failed, falling back to Yahoo Finance")
                df = fetch_ohlcv(args.symbol, period=args.period)
        except Exception as exc:
            print(f"Warning: MT5 error ({exc}), falling back to Yahoo Finance")
            df = fetch_ohlcv(args.symbol, period=args.period)
    else:
        df = fetch_ohlcv(args.symbol, period=args.period)

    df = add_returns(df)

    strategy = _build_strategy(args.strategy, args)
    portfolio = run_paper(
        df,
        strategy,
        args.symbol,
        initial_capital=args.capital,
        risk_per_trade=args.risk,
    )

    print(f"  Final Equity:    ${portfolio.equity:>10,.2f}")
    print(f"  Cash Remaining:  ${portfolio.cash:>10,.2f}")
    print(f"  Total Trades:    {len(portfolio.trades):>10d}")

    if portfolio.trades:
        total_pnl = sum(t.pnl or 0.0 for t in portfolio.trades)
        print(f"  Total P&L:       ${total_pnl:>10,.2f}")

    print("\n  --- Trade Log ---")
    for t in portfolio.trades[:20]:
        pnl_str = f"  P&L: ${t.pnl:,.2f}" if t.pnl is not None else ""
        print(
            f"  {t.time.strftime('%Y-%m-%d %H:%M')} | {t.action:>4} | "
            f"{t.symbol:>6} | {t.shares:>6} @ "
            f"${t.price:>8.2f}{pnl_str}"
        )

    if len(portfolio.trades) > 20:
        print(f"  ... and {len(portfolio.trades) - 20} more trades")

    print(f"\n{'='*60}\n")


def _run_broker(args: argparse.Namespace) -> None:
    action = getattr(args, "broker_command", None)
    if action == "login":
        _broker_login(args)
    elif action == "status":
        _broker_status()
    elif action == "logout":
        if clear_credentials():
            print("Saved MT5 credentials deleted.")
        else:
            print("No saved MT5 credentials found.")


def _broker_login(args: argparse.Namespace) -> None:
    servers = list_headway_servers()
    print("\n  Headway MT5 servers:")
    print(f"    Demo: {', '.join(servers['demo'])}")
    print(f"    Real: {', '.join(servers['real'])}")
    print("  Tip: install MT5 from Headway so these servers are preloaded.\n")

    raw_login = getattr(args, "login", None)
    if raw_login is None:
        entered = input("  MT5 login (account number): ").strip()
        if not entered:
            print("  Login cancelled.")
            return
        raw_login = int(entered)

    raw_server = getattr(args, "server", None)
    demo = bool(getattr(args, "demo", False))
    if raw_server is None and not demo:
        entered = input("  MT5 server [Headway-Demo / Headway-Real]: ").strip()
        raw_server = entered or None
    server = resolve_headway_server(raw_server, demo=demo)

    password = getpass.getpass(f"  MT5 password for {raw_login} on {server}: ")
    if not password:
        print("  Login cancelled (empty password).")
        return

    terminal_path = getattr(args, "terminal_path", None)
    broker = MT5Broker(login=int(raw_login), password=password, server=server)
    if terminal_path:
        broker.terminal_path = terminal_path
    print(f"\n  Connecting to {server} as {raw_login} ...")
    try:
        ok = broker.connect()
    except RuntimeError as exc:
        print(f"\n  {exc}")
        return
    if not ok:
        print("  Login failed. Check login / password / server and retry.")
        return
    try:
        info = broker.get_account_info()
        print(f"  Connected! Balance: {info.balance:.2f} {info.currency}  "
              f"Equity: {info.equity:.2f}")
    finally:
        broker.disconnect()
    path = save_credentials(int(raw_login), password, server)
    print(f"  Credentials saved to {path} (mode 600).")
    print("  Future commands (live/backtest/paper --use-mt5) will reuse them.\n")


def _broker_status() -> None:
    saved = load_credentials()
    if saved is None:
        print(f"No saved credentials ({get_credentials_path()}).")
        print("Run: alice broker login --demo   (or --server Headway-Real)")
        return
    print(f"Saved login: {saved['login']}  server: {saved['server']}")
    print(f"File: {get_credentials_path()}")
    print("Testing connection ...")
    broker = MT5Broker(
        login=int(saved["login"]),
        password=saved["password"],
        server=saved["server"],
    )
    try:
        if not broker.connect():
            print("Connection failed. Re-run 'alice broker login'.")
            return
        info = broker.get_account_info()
        print(f"OK: balance={info.balance:.2f} {info.currency} equity={info.equity:.2f} "
              f"leverage=1:{info.leverage} trade_allowed={info.trade_allowed}")
        positions = broker.get_positions()
        print(f"Open positions: {len(positions)}")
        for pos in positions[:10]:
            side = "BUY" if pos.type == 0 else "SELL"
            print(f"  #{pos.ticket} {side} {pos.symbol} {pos.volume} "
                  f"open={pos.price_open} now={pos.price_current} pnl={pos.profit:.2f}")
    except RuntimeError as exc:
        print(f"{exc}")
    finally:
        if broker.connected:
            broker.disconnect()


def _run_live(args: argparse.Namespace) -> None:
    print(f"\n{'='*60}")
    print(f"  Alice Live Trading — {args.symbol}")
    print(f"  Strategy: {args.strategy}")
    print(f"{'='*60}\n")

    try:
        from typing import Any

        mt5: Any = __import__("MetaTrader5")
    except ImportError:
        print("Error: MetaTrader5 package not installed (Windows only).")
        print("Run on Windows / a Windows VPS with Headway MT5 installed:")
        print("  pip install MetaTrader5")
        sys.exit(1)

    demo = bool(getattr(args, "demo", False))
    raw_server = getattr(args, "server", None)
    login = getattr(args, "login", None)
    password = getattr(args, "password", None)
    if login is None or password is None or raw_server is None:
        saved = load_credentials()
        if saved is not None:
            if login is None:
                login = int(saved["login"])
            if password is None:
                password = saved["password"]
            if raw_server is None:
                raw_server = saved["server"]
    server = resolve_headway_server(raw_server, demo=demo)
    if login is None or password is None:
        print("No MT5 credentials. Run first:")
        print("  alice broker login --demo   # or --server Headway-Real")
        sys.exit(1)

    broker = MT5Broker(login=int(login), password=password, server=server)
    if not broker.connect():
        print("Failed to connect. Check credentials and that MT5 is installed.")
        sys.exit(1)

    execute = bool(getattr(args, "execute", False))
    if execute and not bool(getattr(args, "yes", False)):
        print("  WARNING: --execute places REAL orders on your Headway account.")
        confirm = input("  Type YES to continue with live orders: ").strip()
        if confirm != "YES":
            print("  Aborted. Re-run without --execute for a dry run.")
            broker.disconnect()
            return
    try:
        strategy = _build_strategy(args.strategy, args)

        print(f"Connected to MT5 account #{broker.get_account_info().login} ({server})")
        print(f"Trading {args.symbol} with {args.strategy} "
              f"(risk={args.risk*100:.1f}%, every {args.interval}s)")
        print(f"Mode: {'LIVE ORDERS' if execute else 'SIGNALS ONLY (dry run)'}")
        print("Press Ctrl+C to stop\n")

        import datetime
        import time

        while True:
            try:
                df = broker.get_rates(args.symbol, mt5.TIMEFRAME_H1, 100)
                df = add_returns(df)
                df = strategy.generate_signals(df)

                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                price = float(latest["Close"])

                if latest["Signal"] == 1 and prev["Signal"] != 1:
                    print(f"[{datetime.datetime.now()}] BUY signal {args.symbol} @ {price:.5f}")
                    _handle_signal(broker, args.symbol, True, price, args.risk, execute)
                elif latest["Signal"] == -1 and prev["Signal"] != -1:
                    print(f"[{datetime.datetime.now()}] SELL signal {args.symbol} @ {price:.5f}")
                    _handle_signal(broker, args.symbol, False, price, args.risk, execute)

                positions = broker.get_positions(args.symbol)
                for pos in positions:
                    if pos.type == 0 and latest["Signal"] == -1:
                        print(f"[{datetime.datetime.now()}] Opposite signal: "
                              f"close LONG #{pos.ticket}")
                        if execute:
                            broker.close_position(pos.ticket)
                    elif pos.type == 1 and latest["Signal"] == 1:
                        print(f"[{datetime.datetime.now()}] Opposite signal: "
                              f"close SHORT #{pos.ticket}")
                        if execute:
                            broker.close_position(pos.ticket)

                time.sleep(args.interval)

            except KeyboardInterrupt:
                print("\nStopping live trading...")
                break
            except Exception as exc:
                print(f"Error in trading loop: {exc} (retrying)")
                import time as _time

                _time.sleep(args.interval)

    finally:
        broker.disconnect()
        print("Disconnected from MT5")


def _handle_signal(
    broker: MT5Broker,
    symbol: str,
    is_buy: bool,
    price: float,
    risk: float,
    execute: bool,
) -> None:
    """Size a position from equity risk and optionally submit it."""
    account = broker.get_account_info()
    risk_amount = account.equity * risk
    stop_distance = price * 0.02  # simplified 2% stop
    if stop_distance <= 0:
        return
    lots = max(0.01, round(risk_amount / (stop_distance * 100000), 2))
    side = "BUY" if is_buy else "SELL"
    stop = price * (0.98 if is_buy else 1.02)
    target = price * (1.04 if is_buy else 0.96)
    print(f"  {side} {lots} lots @ {price:.5f}  SL={stop:.5f} TP={target:.5f}")
    if not execute:
        print("  Dry run: add --execute to place the order.")
        return
    if is_buy:
        broker.buy(symbol, lots, stop, target, "Alice Bot Signal")
    else:
        broker.sell(symbol, lots, stop, target, "Alice Bot Signal")


def _run_webhook(args: argparse.Namespace) -> None:
    print(f"\n{'='*60}")
    print("  Alice Webhook Server")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"{'='*60}\n")

    receiver = TradingViewSignalReceiver(secret=args.secret)
    app = create_webhook_app(receiver, args.host, args.port)

    if app is None:
        print("Error: Flask not installed. Install with: pip install -e '.[web]'")
        sys.exit(1)

    try:
        import os

        os.environ["FLASK_ENV"] = "development"
        app.run(host=args.host, port=args.port, debug=True)
    except KeyboardInterrupt:
        print("\nShutting down webhook server...")


def _run_dashboard(args: argparse.Namespace) -> None:
    print(f"\n{'='*60}")
    print("  Alice Dashboard")
    print(f"  Open: http://{args.host}:{args.port}")
    print(f"{'='*60}\n")

    try:
        from open_alice.dashboard.app import create_dashboard_app
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    app = create_dashboard_app()
    try:
        app.run(host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")


if __name__ == "__main__":
    main()
