"""
This module defines Pydantic models for API responses.
"""

from typing import Any, List, Optional, TypedDict


class Kline(TypedDict):
    """Represents a single kline/candlestick data point."""

    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    quote_asset_volume: str
    number_of_trades: int
    taker_buy_base_asset_volume: str
    taker_buy_quote_asset_volume: str
    ignore: str


class Ticker(TypedDict):
    """Represents a price ticker for a single symbol."""

    symbol: str
    price: str


class Fill(TypedDict):
    """Represents a single fill for an order."""

    price: str
    qty: str
    commission: str
    commissionAsset: str
    tradeId: int


class Order(TypedDict):
    """Represents a single order."""

    symbol: str
    orderId: int
    orderListId: int
    clientOrderId: str
    transactTime: int
    price: str
    origQty: str
    executedQty: str
    cummulativeQuoteQty: str
    status: str
    timeInForce: str
    type: str
    side: str
    stopPrice: str
    time: int
    updateTime: int
    isWorking: bool
    fills: List["Fill"]


class OcoOrder(TypedDict):
    """Represents an OCO order response."""

    symbol: str
    orderListId: int
    contingencyType: str
    listStatusType: str
    listOrderStatus: str
    listClientOrderId: str
    transactionTime: int
    orders: List[dict[str, Any]]
    orderReports: List[Order]


class Balance(TypedDict):
    """Represents the balance of a single asset."""

    asset: str
    free: str
    locked: str


class Trade(TypedDict):
    """Represents a single trade."""

    id: int
    orderId: int
    price: str
    qty: str
    commission: str
    commissionAsset: str
    time: int
    permissions: List[str]
    total_portfolio_value: float
    balances: List[Balance]


class AccountInfo(TypedDict):
    """Represents the user's account information."""

    balances: List[Balance]
    canTrade: bool
    canWithdraw: bool
    canDeposit: bool
    updateTime: int
    accountType: str
    permissions: List[str]


class RateLimit(TypedDict):
    """Represents a rate limit for the API."""

    rateLimitType: str
    interval: str
    intervalNum: int
    limit: int


class SymbolFilter(TypedDict):
    """Represents a filter for a symbol, defining trading rules."""

    filterType: str
    minPrice: Optional[str]
    maxPrice: Optional[str]
    tickSize: Optional[str]
    minQty: Optional[str]
    maxQty: Optional[str]
    stepSize: Optional[str]
    minNotional: Optional[str]


class SymbolInfo(TypedDict):
    """Represents information about a single symbol."""

    symbol: str
    status: str
    baseAsset: str
    baseAssetPrecision: int
    quoteAsset: str
    quoteAssetPrecision: int
    orderTypes: List[str]
    icebergAllowed: bool
    ocoAllowed: bool
    isSpotTradingAllowed: bool
    isMarginTradingAllowed: bool
    filters: List[SymbolFilter]
    permissions: List[str]


class ExchangeInfo(TypedDict):
    """Represents the overall exchange information."""

    timezone: str
    serverTime: int
    rateLimits: List[RateLimit]
    symbols: List[SymbolInfo]
