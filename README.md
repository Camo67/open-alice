# open-alice

> Alice — an open-source AI trading bot covering equities, crypto, commodities, forex, and macro.

## Features

- **Multi-asset support** — equities, crypto, commodities, forex
- **Strategy engine** — pluggable strategies with backtesting
- **Risk management** — position sizing, stop-loss, take-profit
- **Paper trading** — test without real money
- **Live trading** — connect to MetaTrader 5 for execution
- **Signal integration** — receive signals from TradingView and other platforms via webhooks
- **CLI interface** — simple command-line controls

## Quick Start

```bash
# Install
pip install -e .

# For webhook server functionality
pip install -e ".[web]"

# Run paper trading
alice paper --strategy sma_crossover --symbol AAPL

# Backtest
alice backtest --strategy sma_crossover --symbol AAPL --period 1y

# Live trading (requires MetaTrader 5 terminal running)
alice live --symbol EURUSD --strategy sma_crossover --login 12345678 --password your_password --server your_server

# Start webhook server for signals (e.g., from TradingView)
alice serve --host 0.0.0.0 --port 5000
```

## Project Structure

```
open-alice/
├── src/
│   └── open_alice/
│       ├── __init__.py
│       ├── __main__.py
│       ├── broker/         # Broker integrations
│       │   ├── __init__.py
│       │   └── mt5.py      # MetaTrader 5 integration
│       ├── cli.py          # CLI entry point
│       ├── data.py         # Market data fetching
│       ├── engine/         # Backtesting & execution engine
│       ├── signals/        # Signal reception
│       │   ├── __init__.py
│       │   └── webhook.py  # Webhook signal receiver
│       ├── strategies/     # Trading strategies
│       └── risk/           # Risk management
├── tests/
├── .github/
│   └── workflows/
│       └── ci.yml         # GitHub Actions CI
├── Dockerfile             # Container build instructions
└── docker-compose.yml     # Easy deployment configuration
```

## License

AGPL-3.0