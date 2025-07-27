"""
This module defines TypedDict models for API responses.
"""

from typing import Any, TypedDict

# Raw kline data from Binance API - list of values in specific order
RawKline = list[Any]  # [open_time, open, high, low, close, volume, close_time, ...]


class Kline(TypedDict):  # noqa: vulture
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


class Ticker(TypedDict):  # noqa: vulture
    """Represents a price ticker for a single symbol."""

    symbol: str
    price: str


class Fill(TypedDict):  # noqa: vulture
    """Represents a single fill for an order."""

    price: str
    qty: str
    commission: str
    commissionAsset: str
    tradeId: int


class Order(TypedDict):  # noqa: vulture
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
    fills: list["Fill"]


class OcoOrder(TypedDict):
    """Represents an OCO order response."""

    symbol: str
    orderListId: int
    contingencyType: str
    listStatusType: str
    listOrderStatus: str
    listClientOrderId: str
    transactionTime: int
    orders: list[dict[str, Any]]
    orderReports: list[Order]


class Balance(TypedDict):
    """Represents the balance of a single asset."""

    asset: str
    free: str
    locked: str


class ProcessedBalance(TypedDict):
    """Represents a processed balance with calculated values."""

    asset: str
    free: float
    locked: float
    total: float
    value_usdt: float


class Trade(TypedDict):
    """Represents a single trade."""

    id: int
    orderId: int
    price: str
    qty: str
    commission: str
    commissionAsset: str
    time: int
    permissions: list[str]
    total_portfolio_value: float
    balances: list[Balance]


class AccountInfo(TypedDict):  # noqa: vulture
    """Represents the user's account information."""

    balances: list[Balance]
    canTrade: bool
    canWithdraw: bool
    canDeposit: bool
    updateTime: int
    accountType: str
    permissions: list[str]


class APIErrorResponse(TypedDict):
    """Represents an API error response."""

    code: int
    msg: str


class ServerTimeResponse(TypedDict):
    """Represents a server time response."""

    serverTime: int


class TickerPriceResponse(TypedDict):
    """Represents a ticker price response."""

    symbol: str
    price: str


class ValidationError(TypedDict):
    """Represents a validation error message."""

    type: str
    message: str
    suggestion: str | None


class RateLimit(TypedDict):
    """Represents a rate limit for the API."""

    rateLimitType: str
    interval: str
    intervalNum: int
    limit: int


class SymbolFilter(TypedDict):
    """Represents a filter for a symbol, defining trading rules."""

    filterType: str
    minPrice: str | None
    maxPrice: str | None
    tickSize: str | None
    minQty: str | None
    maxQty: str | None
    stepSize: str | None
    minNotional: str | None


class SymbolInfo(TypedDict):
    """Represents information about a single symbol."""

    symbol: str
    status: str
    baseAsset: str
    baseAssetPrecision: int
    quoteAsset: str
    quoteAssetPrecision: int
    orderTypes: list[str]
    icebergAllowed: bool
    ocoAllowed: bool
    isSpotTradingAllowed: bool
    isMarginTradingAllowed: bool
    filters: list[SymbolFilter]
    permissions: list[str]


class ExchangeInfo(TypedDict):
    """Represents the overall exchange information."""

    timezone: str
    serverTime: int
    rateLimits: list[RateLimit]
    symbols: list[SymbolInfo]
