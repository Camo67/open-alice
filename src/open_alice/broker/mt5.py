"""MetaTrader 5 broker integration (works with Headway accounts)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd


def _load_mt5() -> Any:
    """Import the MetaTrader5 package lazily with a helpful error."""
    try:
        from importlib import import_module

        return import_module("MetaTrader5")
    except ImportError as exc:
        raise RuntimeError(
            "The MetaTrader5 package is not installed or not supported on this "
            "platform. It officially supports Windows only. Install the Headway "
            "MT5 terminal on Windows (or a Windows VPS / Wine), then run "
            "'pip install MetaTrader5'. Original error: "
            f"{exc}"
        ) from exc


@dataclass
class MT5AccountInfo:
    """Account information from MT5."""

    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    leverage: int
    trade_allowed: bool
    trade_expert: bool
    connected: bool


@dataclass
class MT5Position:
    """Position information from MT5."""

    ticket: int
    symbol: str
    type: int  # 0 for buy, 1 for sell
    volume: float
    price_open: float
    price_current: float
    profit: float
    swap: float
    commission: float
    comment: str


class MT5Broker:
    """MetaTrader 5 broker interface (incl. Headway servers)."""

    def __init__(
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        timeout: int = 60000,
        terminal_path: str | None = None,
    ) -> None:
        """Initialize MT5 broker connection.

        Args:
            login: MT5 account login (if None, attaches to the open terminal).
            password: MT5 account password.
            server: MT5 server name, e.g. Headway-Demo or Headway-Real.
            timeout: Connection timeout in milliseconds.
            terminal_path: Optional path to terminal64.exe (useful under Wine).
        """
        self.login = login
        self.password = password
        self.server = server
        self.timeout = timeout
        self.terminal_path = terminal_path
        self.connected = False
        self.account_info: MT5AccountInfo | None = None

    def connect(self) -> bool:
        """Initialize connection to the MT5 terminal.

        Returns:
            True if connection succeeded, False otherwise.
        """
        mt5 = _load_mt5()
        kwargs: dict[str, Any] = {"timeout": self.timeout}
        if self.terminal_path:
            kwargs["path"] = self.terminal_path
        if self.login is not None:
            kwargs["login"] = self.login
        if self.password is not None:
            kwargs["password"] = self.password
        if self.server is not None:
            kwargs["server"] = self.server
        if not mt5.initialize(**kwargs):
            print(f"MT5 initialize() failed, error code = {mt5.last_error()}")
            print("Check: MT5 terminal installed, login/password/server correct.")
            return False

        self.connected = True
        self.account_info = self._get_account_info()
        print(f"Connected to MT5 account #{self.account_info.login}")
        return True

    def disconnect(self) -> None:
        """Disconnect from the MT5 terminal."""
        if not self.connected:
            return
        mt5 = _load_mt5()
        mt5.shutdown()
        self.connected = False
        print("Disconnected from MT5")

    def _require_connected(self) -> Any:
        if not self.connected:
            raise ConnectionError("Not connected to MT5. Call connect() first.")
        return _load_mt5()

    def _get_account_info(self) -> MT5AccountInfo:
        """Fetch account information from MT5."""
        mt5 = self._require_connected()
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"Failed to get account info: {mt5.last_error()}")
        return MT5AccountInfo(
            login=int(info.login),
            balance=float(info.balance),
            equity=float(info.equity),
            margin=float(info.margin),
            free_margin=float(info.margin_free),
            margin_level=float(info.margin_level),
            currency=str(info.currency),
            leverage=int(info.leverage),
            trade_allowed=bool(info.trade_allowed),
            trade_expert=bool(info.trade_expert),
            connected=True,
        )

    def get_account_info(self) -> MT5AccountInfo:
        """Return current account information."""
        return self._get_account_info()

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Return symbol info, selecting the symbol in MarketWatch if needed."""
        mt5 = self._require_connected()
        info = mt5.symbol_info(symbol)
        if info is None:
            if not mt5.symbol_select(symbol, True):
                raise ValueError(f"Symbol {symbol} not found: {mt5.last_error()}")
            info = mt5.symbol_info(symbol)
            if info is None:
                raise RuntimeError(f"Failed to get symbol info for {symbol}")
        result: dict[str, Any] = dict(info._asdict())
        return result

    def get_rates(self, symbol: str, timeframe: int, count: int = 1000) -> pd.DataFrame:
        """Return recent OHLCV bars as a DataFrame indexed by time."""
        mt5 = self._require_connected()
        self.get_symbol_info(symbol)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            raise RuntimeError(f"Failed to get rates for {symbol}: {mt5.last_error()}")
        return _rates_to_frame(rates)

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """Return OHLCV data between two dates (for backtesting)."""
        mt5 = self._require_connected()
        timeframe_map = {
            "1M": mt5.TIMEFRAME_M1,
            "5M": mt5.TIMEFRAME_M5,
            "15M": mt5.TIMEFRAME_M15,
            "30M": mt5.TIMEFRAME_M30,
            "1H": mt5.TIMEFRAME_H1,
            "4H": mt5.TIMEFRAME_H4,
            "1D": mt5.TIMEFRAME_D1,
            "1W": mt5.TIMEFRAME_W1,
            "1MN": mt5.TIMEFRAME_MN1,
        }
        if timeframe not in timeframe_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        self.get_symbol_info(symbol)
        rates = mt5.copy_rates_range(symbol, timeframe_map[timeframe], start_date, end_date)
        if rates is None:
            raise RuntimeError(f"Failed to get historical data for {symbol}")
        df = _rates_to_frame(rates)
        mask = (df.index >= start_date) & (df.index <= end_date)
        return df.loc[mask]

    def get_positions(self, symbol: str | None = None) -> list[MT5Position]:
        """Return open positions, optionally filtered by symbol."""
        mt5 = self._require_connected()
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            return []
        return [
            MT5Position(
                ticket=int(pos.ticket),
                symbol=str(pos.symbol),
                type=int(pos.type),
                volume=float(pos.volume),
                price_open=float(pos.price_open),
                price_current=float(pos.price_current),
                profit=float(pos.profit),
                swap=float(pos.swap),
                commission=float(pos.commission),
                comment=str(pos.comment),
            )
            for pos in positions
        ]

    def place_order(
        self,
        symbol: str,
        order_type: int,
        volume: float,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "Alice Bot",
        deviation: int = 10,
    ) -> bool:
        """Place a market deal order."""
        mt5 = self._require_connected()
        symbol_info = self.get_symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No tick data for {symbol}")
        if price <= 0.0:
            is_buy = order_type == mt5.ORDER_TYPE_BUY
            price = float(tick.ask if is_buy else tick.bid)
        request: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": symbol_info.get("filling_mode", mt5.ORDER_FILLING_IOC),
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            code = result.retcode if result is not None else mt5.last_error()
            print(f"Order send failed, retcode={code}")
            return False
        print(f"Order placed successfully: {result.order}")
        return True

    def buy(
        self,
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "Alice Bot",
    ) -> bool:
        """Place a market buy order."""
        mt5 = self._require_connected()
        return self.place_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_BUY,
            volume=volume,
            sl=sl,
            tp=tp,
            comment=comment,
        )

    def sell(
        self,
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "Alice Bot",
    ) -> bool:
        """Place a market sell order."""
        mt5 = self._require_connected()
        return self.place_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_SELL,
            volume=volume,
            sl=sl,
            tp=tp,
            comment=comment,
        )

    def close_position(self, ticket: int) -> bool:
        """Close an open position by ticket."""
        mt5 = self._require_connected()
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            print(f"Position {ticket} not found")
            return False
        pos = positions[0]
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            raise RuntimeError(f"No tick data for {pos.symbol}")
        is_long = pos.type == mt5.ORDER_TYPE_BUY
        request: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY,
            "price": float(tick.bid if is_long else tick.ask),
            "deviation": 10,
            "magic": 234000,
            "comment": "Alice Bot Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            code = result.retcode if result is not None else mt5.last_error()
            print(f"Position close failed, retcode={code}")
            return False
        print(f"Position {ticket} closed successfully")
        return True


def _rates_to_frame(rates: Any) -> pd.DataFrame:
    """Convert MT5 rates array to an OHLCV DataFrame."""
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")
    df = df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "tick_volume": "Volume",
        }
    )
    return df
