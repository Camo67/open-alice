"""Webhook receiver for trading signals (e.g., TradingView alerts)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals."""

    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"


@dataclass
class TradingSignal:
    """Represents a trading signal received from external source."""

    symbol: str
    signal_type: SignalType
    price: float | None = None
    timestamp: datetime | None = None
    strength: float | None = None  # Signal strength 0-1
    stop_loss: float | None = None
    take_profit: float | None = None
    comment: str | None = None
    raw_data: dict[str, Any] | None = None


class SignalReceiver:
    """Base class for signal receivers."""

    def parse_signal(self, raw_data: dict[str, Any]) -> TradingSignal | None:
        """Parse raw data into a TradingSignal.

        Args:
            raw_data: Raw data received from external source.

        Returns:
            TradingSignal or None if parsing failed.
        """
        raise NotImplementedError


def _opt_float(raw_data: dict[str, Any], key: str) -> float | None:
    """Return float(raw_data[key]) or None when the key is missing/null."""
    value = raw_data.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning("Could not parse numeric field %s: %r", key, value)
        return None


def _opt_str(raw_data: dict[str, Any], key: str) -> str | None:
    """Return str(raw_data[key]) or None when the key is missing/null."""
    value = raw_data.get(key)
    if value is None:
        return None
    return str(value)


class TradingViewSignalReceiver(SignalReceiver):
    """Receiver for TradingView webhook alerts."""

    def __init__(self, secret: str | None = None) -> None:
        """Initialize TradingView signal receiver.

        Args:
            secret: Optional secret for validating requests.
        """
        self.secret = secret

    def parse_signal(self, raw_data: dict[str, Any]) -> TradingSignal | None:
        """Parse TradingView webhook alert into TradingSignal.

        Expected TradingView alert format:
        {
            "symbol": "AAPL",
            "action": "buy",
            "price": 150.00,
            "time": "2023-01-01T10:30:00Z",
            "strength": 0.8,
            "stop_loss": 145.00,
            "take_profit": 160.00,
            "comment": "My strategy signal"
        }

        Args:
            raw_data: Raw webhook data from TradingView.

        Returns:
            TradingSignal or None if parsing failed.
        """
        try:
            # Validate required fields
            if "symbol" not in raw_data or "action" not in raw_data:
                logger.warning("Missing required fields in TradingView signal")
                return None

            symbol = str(raw_data["symbol"]).upper()
            action = str(raw_data["action"]).lower()

            # Map action to signal type
            if action in ["buy", "long"]:
                signal_type = SignalType.BUY
            elif action in ["sell", "short"]:
                signal_type = SignalType.SELL
            elif action in ["close", "exit"]:
                signal_type = SignalType.CLOSE
            else:
                logger.warning("Unknown action in TradingView signal: %s", action)
                return None

            # Parse timestamp
            timestamp: datetime | None = None
            raw_time = raw_data.get("time")
            if raw_time is not None:
                try:
                    timestamp = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
                except ValueError:
                    logger.warning("Could not parse timestamp: %s", raw_time)
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                price=_opt_float(raw_data, "price"),
                timestamp=timestamp,
                strength=_opt_float(raw_data, "strength"),
                stop_loss=_opt_float(raw_data, "stop_loss"),
                take_profit=_opt_float(raw_data, "take_profit"),
                comment=_opt_str(raw_data, "comment"),
                raw_data=raw_data,
            )

        except Exception as exc:
            logger.error("Error parsing TradingView signal: %s", exc)
            return None


# Simple HTTP server for receiving webhooks (optional)
def create_webhook_app(receiver: SignalReceiver, host: str = "0.0.0.0", port: int = 5000) -> Any:
    """Create a simple Flask app for receiving webhook signals.

    Args:
        receiver: SignalReceiver instance to use for parsing.
        host: Host to bind to (used by callers running the app).
        port: Port to bind to (used by callers running the app).

    Returns:
        Flask app instance, or None when Flask is not installed.
    """
    try:
        from flask import Flask, jsonify, request

        app = Flask(__name__)

        @app.route("/webhook", methods=["POST"])  # type: ignore[untyped-decorator]
        def webhook() -> Any:
            if not request.is_json:
                return jsonify({"error": "Expected JSON"}), 400

            data = request.get_json()
            signal = receiver.parse_signal(data)

            if signal is None:
                return jsonify({"error": "Failed to parse signal"}), 400

            logger.info("Received signal: %s", signal)
            return jsonify({"status": "received", "signal": signal.__dict__}), 200

        @app.route("/health", methods=["GET"])  # type: ignore[untyped-decorator]
        def health() -> Any:
            return jsonify({"status": "healthy"}), 200

        return app

    except ImportError:
        logger.warning("Flask not installed. Webhook server not available.")
        return None
