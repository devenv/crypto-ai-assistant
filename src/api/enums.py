"""
This module defines enumeration types used throughout the Crypto AI Assistant application.
"""

from enum import Enum


class OrderSide(str, Enum):
    """Represents the side of an order."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Represents the type of an order."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"
    OCO = "OCO"  # One-Cancels-the-Other


class TimeInForce(str, Enum):
    """Represents the time in force for an order."""

    GTC = "GTC"  # Good 'Til Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class CancelOrderType(str, Enum):
    """Represents the type of entity to cancel for the CLI."""

    ORDER = "order"
    OCO = "oco"
