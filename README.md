# open-alice

> Alice — an open-source AI trading bot covering equities, crypto, commodities, forex, and macro.

## Features

- **Multi-asset support** — equities, crypto, commodities, forex
- **Strategy engine** — pluggable strategies with backtesting
- **Risk management** — position sizing, stop-loss, take-profit
- **Paper trading** — test without real money
- **CLI interface** — simple command-line controls

## Quick Start

```bash
# Install
pip install -e .

# Run paper trading
alice paper --strategy sma_crossover --symbol AAPL

# Backtest
alice backtest --strategy sma_crossover --symbol AAPL --start 2024-01-01 --end 2025-01-01
```

## Project Structure

```
open-alice/
├── src/
│   └── open_alice/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py          # CLI entry point
│       ├── data.py         # Market data fetching
│       ├── strategies/     # Trading strategies
│       ├── engine/         # Backtesting & execution engine
│       └── risk/           # Risk management
└── tests/
```

## License

AGPL-3.0
