"""Webhook receiver for trading signals (e.g., TradingView alerts)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

import logging

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
    price: Optional[float] = None
    timestamp: Optional[datetime] = None
    strength: Optional[float] = None  # Signal strength 0-1
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class SignalReceiver:
    """Base class for signal receivers."""
    
    def parse_signal(self, raw_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Parse raw data into a TradingSignal.
        
        Args:
            raw_data: Raw data received from external source
            
        Returns:
            TradingSignal or None if parsing failed
        """
        raise NotImplementedError


class TradingViewSignalReceiver(SignalReceiver):
    """Receiver for TradingView webhook alerts."""
    
    def __init__(self, secret: Optional[str] = None):
        """Initialize TradingView signal receiver.
        
        Args:
            secret: Optional secret for validating requests
        """
        self.secret = secret
    
    def parse_signal(self, raw_data: Dict[str, Any]) -> Optional[TradingSignal]:
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
            raw_data: Raw webhook data from TradingView
            
        Returns:
            TradingSignal or None if parsing failed
        """
        try:
            # Validate required fields
            if "symbol" not in raw_data or "action" not in raw_data:
                logger.warning("Missing required fields in TradingView signal")
                return None
            
            symbol = raw_data["symbol"].upper()
            action = raw_data["action"].lower()
            
            # Map action to signal type
            if action in ["buy", "long"]:
                signal_type = SignalType.BUY
            elif action in ["sell", "short"]:
                signal_type = SignalType.SELL
            elif action in ["close", "exit"]:
                signal_type = SignalType.CLOSE
            else:
                logger.warning(f"Unknown action in TradingView signal: {action}")
                return None
            
            # Parse optional fields
            price = float(raw_data["price"]) if "price" in raw_data and raw_data["price"] is not None else None
            strength = float(raw_data["strength"]) if "strength" in raw_data and raw_data["strength"] is not None else None
            stop_loss = float(raw_data["stop_loss"]) if "stop_loss" in raw_data and raw_data["stop_loss"] is not None else None
            take_profit = float(raw_data["take_profit"]) if "take_profit" in raw_data and raw_data["take_profit"] is not None else None
            comment = str(raw_data["comment"]) if "comment" in raw_data and raw_data["comment"] is not None else None
            
            # Parse timestamp
            timestamp = None
            if "time" in raw_data and raw_data["time"] is not None:
                try:
                    timestamp = datetime.fromisoformat(raw_data["time"].replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(f"Could not parse timestamp: {raw_data['time']}")
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                price=price,
                timestamp=timestamp,
                strength=strength,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment,
                raw_data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing TradingView signal: {e}")
            return None


# Simple HTTP server for receiving webhooks (optional)
def create_webhook_app(receiver: SignalReceiver, host: str = "0.0.0.0", port: int = 5000):
    """Create a simple Flask app for receiving webhook signals.
    
    Args:
        receiver: SignalReceiver instance to use for parsing
        host: Host to bind to
        port: Port to bind to
        
    Returns:
        Flask app instance
    """
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            if not request.is_json:
                return jsonify({"error": "Expected JSON"}), 400
            
            data = request.get_json()
            signal = receiver.parse_signal(data)
            
            if signal is None:
                return jsonify({"error": "Failed to parse signal"}), 400
            
            # In a real implementation, this would queue the signal for processing
            logger.info(f"Received signal: {signal}")
            return jsonify({"status": "received", "signal": signal.__dict__}), 200
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy"}), 200
        
        return app
        
    except ImportError:
        logger.warning("Flask not installed. Webhook server not available.")
        return None