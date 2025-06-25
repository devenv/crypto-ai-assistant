"""
This module provides a client for interacting with the Binance API.
"""

from api.enums import CancelOrderType, OrderSide, OrderType, TimeInForce
from api.exceptions import APIError, BinanceException, InsufficientFundsError, InvalidSymbolError
from api.models import (
    AccountInfo,
    Balance,
    ExchangeInfo,
    Fill,
    Kline,
    Order,
    RateLimit,
    SymbolFilter,
    SymbolInfo,
    Ticker,
    Trade,
)

__all__ = [
    "APIError",
    "BinanceException",
    "InsufficientFundsError",
    "InvalidSymbolError",
    "OrderSide",
    "OrderType",
    "TimeInForce",
    "CancelOrderType",
    "Kline",
    "Ticker",
    "Fill",
    "Order",
    "Trade",
    "Balance",
    "AccountInfo",
    "RateLimit",
    "SymbolFilter",
    "SymbolInfo",
    "ExchangeInfo",
]
