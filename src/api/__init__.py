"""
This module provides a client for interacting with the Binance API.
"""

from .client import BinanceClient
from .enums import CancelOrderType, OrderSide, OrderType, TimeInForce
from .exceptions import (
    APIError,
    BinanceException,
    InsufficientFundsError,
    InvalidSymbolError,
)
from .models import (
    AccountInfo,
    Balance,
    ExchangeInfo,
    Fill,
    Kline,
    OcoOrder,
    Order,
    RateLimit,
    SymbolFilter,
    SymbolInfo,
    Ticker,
    Trade,
)

__all__ = [
    # Enums
    "CancelOrderType",
    "OrderSide",
    "OrderType",
    "TimeInForce",
    # Exceptions
    "APIError",
    "BinanceException",
    "InsufficientFundsError",
    "InvalidSymbolError",
    # Models
    "AccountInfo",
    "Balance",
    "ExchangeInfo",
    "Fill",
    "Kline",
    "Order",
    "RateLimit",
    "SymbolFilter",
    "SymbolInfo",
    "Ticker",
    "Trade",
    "OcoOrder",
    # Client
    "BinanceClient",
]
