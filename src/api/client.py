"""Binance API Client Module.

This module provides a comprehensive client for interacting with the Binance
REST API, including authentication, request signing, and error handling.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from json import JSONDecodeError
from typing import Any, NoReturn, TypedDict, cast
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from .enums import OrderSide, OrderType, TimeInForce
from .exceptions import (
    APIError,
    BinanceException,
    InsufficientFundsError,
    InvalidSymbolError,
)
from .models import (
    AccountInfo,
    ExchangeInfo,
    Order,
    ProcessedBalance,
    RawKline,
    ServerTimeResponse,
    Ticker,
    Trade,
)

# Configure logging
logger = logging.getLogger(__name__)


class ErrorResponse(TypedDict):
    """Represents an error response from Binance API."""

    code: int
    msg: str


# Union type for all possible API responses
# Note: ErrorResponse is also a dict, but we keep it separate for clarity
APIResponse = dict[str, Any] | ErrorResponse


class BinanceClient:
    """
    A client for interacting with the Binance REST API.

    This client handles authentication, request signing, and response parsing
    for both public and private endpoints.

    Attributes:
        base_url (str): The base URL for the Binance API.
    """

    def __init__(self, base_url: str = "https://api.binance.com") -> None:
        """Initializes the BinanceClient.

        Loads API keys from environment variables (`BINANCE_API_KEY` and
        `BINANCE_API_SECRET`) and sets up a session for making requests.

        Args:
            base_url: The base URL for the Binance API. Defaults to "https://api.binance.com".

        Raises:
            ValueError: If the API keys are not found in the environment.
        """
        load_dotenv()
        self.base_url = base_url
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        if not self.api_key or not self.api_secret:
            logger.error("Binance API Key and Secret must be set as environment variables.")
            raise ValueError("API keys not found in environment.")

        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        self._cache: dict[str, ExchangeInfo] = {}
        self._cache_expirations: dict[str, float] = {}

    def _get_timestamp(self) -> int:
        """Get the current time in milliseconds.

        Returns:
            The current timestamp.
        """
        return int(time.time() * 1000)

    def _generate_signature(self, query_string: str) -> str:
        """Generate a SHA256 signature for a query string.

        Args:
            query_string: The URL-encoded query string.

        Returns:
            The HMAC SHA256 signature.

        Raises:
            ValueError: If the API secret is not configured.
        """
        if not self.api_secret:
            # This should not be reached if __init__ completes successfully
            raise ValueError("API secret not configured.")  # pragma: no cover
        return hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def _request(self, method: str, endpoint: str, params: dict[str, Any] | None = None, signed: bool = True) -> dict[str, Any]:
        """Send a request to the Binance API.

        Args:
            method: The HTTP method (e.g., "GET", "POST").
            endpoint: The API endpoint path.
            params: A dictionary of request parameters.
            signed: Whether the request needs to be signed.

        Returns:
            The JSON response from the API.

        Raises:
            APIError: If the API request fails.
        """
        request_params = params.copy() if params else {}

        if signed:
            request_params["timestamp"] = self._get_timestamp()
            query_string = urlencode(request_params)
            request_params["signature"] = self._generate_signature(query_string)
        else:
            query_string = urlencode(request_params)

        try:
            response: requests.Response = self.session.request(
                method=method.upper(),
                url=f"{self.base_url}{endpoint}",
                params=request_params if method.upper() in ["GET", "DELETE"] else None,
                data=request_params if method.upper() == "POST" else None,
            )
            response.raise_for_status()
            # Cast the result to the expected API response type to satisfy mypy
            json_response = cast(APIResponse, response.json())
            return self._handle_response(json_response)
        except requests.exceptions.RequestException as e:
            self._handle_requests_exception(e)

    def _handle_requests_exception(self, e: requests.exceptions.RequestException) -> NoReturn:
        """Handle requests exceptions and convert them to APIError.

        Args:
            e: The requests exception to handle.

        Raises:
            APIError: Always raises an APIError with details from the exception.
        """
        response: requests.Response | None = e.response
        status_code = response.status_code if response else None
        error_details = ""
        if response and hasattr(response, "text"):
            try:
                error_json = response.json()
                error_details = f" - Details: {error_json}"
            except (ValueError, JSONDecodeError):
                error_details = f" - Response: {response.text}"
        raise APIError(f"{str(e)}{error_details}", status_code=status_code) from e

    def _handle_response(self, response: APIResponse) -> dict[str, Any]:
        """Handles the Binance API response, checking for errors with enhanced error categorization.

        Args:
            response: The response from the API.

        Returns:
            The response if no error is detected.

        Raises:
            BinanceException: If a Binance-specific error is detected.
            InvalidSymbolError: If the symbol is invalid.
            InsufficientFundsError: If there are insufficient funds.
            APIError: For other API errors.
        """
        # Check if response contains an error
        if "code" in response and response["code"] != 0:
            # Type assertion for error response handling
            assert isinstance(response["code"], int | str), f"Expected int or str for code, got {type(response['code'])}"
            assert isinstance(response.get("msg"), str | type(None)), f"Expected str or None for msg, got {type(response.get('msg'))}"

            error_code: int = int(response["code"])
            error_msg: str = str(response.get("msg", "Unknown error"))

            # Enhanced error handling with specific error codes and recovery suggestions
            error_suggestions: dict[int, str] = {
                -1000: "Check your request format and parameters",
                -1001: "Server is experiencing issues - try again in a few moments",
                -1002: "Request was not authorized - check API keys and permissions",
                -1003: "Too many requests - please reduce request frequency",
                -1006: "Server is currently unavailable - try again later",
                -1007: "Request timeout - consider reducing complexity or try again",
                -1013: "Invalid quantity precision - check lot size requirements",
                -1014: "Unknown order type - use supported order types only",
                -1015: "Invalid time in force value",
                -1016: "Invalid order side - use BUY or SELL",
                -1020: "Unsupported operation for this endpoint",
                -1021: "Request timestamp is invalid - check system clock",
                -1022: "Invalid signature - verify API secret and signature generation",
                -1121: "Invalid symbol - check symbol format and market availability",
                -2010: "NEW_ORDER_REJECTED - check order parameters and account status",
                -2011: "Order was canceled due to market conditions",
                -2013: "Order does not exist - check order ID",
                -2014: "Invalid API key format - verify API key is correct",
                -2015: "Invalid API key, IP, or permissions - check API settings",
                -2016: "Trading is disabled for this account",
                -2018: "Account balance is insufficient for this order",
                -2019: "Account margin is insufficient",
                -2020: "Unable to place order - risk management rules triggered",
                -2021: "Order would immediately match and take - adjust price",
                -2022: "Order would trigger stop condition immediately",
                -2025: "Invalid order type for current market conditions",
                -2026: "Order price is too high compared to market price",
                -2027: "Order price is too low compared to market price",
                -2028: "Position side does not match order side",
                -2029: "Invalid order position side",
                -3008: "Symbol is not supported for this operation",
                -3010: "Account has insufficient balance for this symbol",
                -3011: "Rest API trading is not enabled for this account",
                -3012: "Account is restricted from trading",
                -3013: "Order price precision exceeds maximum allowed",
                -3014: "Order quantity precision exceeds maximum allowed",
                -3015: "Order quantity is below minimum required",
                -3016: "Order price is below minimum required",
                -3017: "Order quantity exceeds maximum allowed",
                -3018: "Order price exceeds maximum allowed",
                -3019: "Order notional value is below minimum required",
                -3020: "Order notional value exceeds maximum allowed",
                -3021: "Order would cause position to exceed risk limits",
                -3022: "Reduce-only order exceeds position size",
                -4000: "Invalid order status for this operation",
                -4001: "Order quantity exceeds available balance",
                -4002: "Account does not have sufficient margin",
                -4003: "Position does not exist",
                -4004: "Invalid position side",
                -4005: "Position side is being modified",
                -4006: "Position margin is insufficient",
                -4007: "Isolated margin account cannot be transferred to cross margin",
                -4008: "Cross margin account cannot be transferred to isolated margin",
                -4009: "Transfer amount exceeds available balance",
                -4010: "Transfer is not allowed for this asset",
                -4011: "Maximum number of open orders reached",
                -4012: "API key does not have permission for this operation",
                -4013: "Invalid symbol for this market",
                -4014: "Order size is too small for this symbol",
                -4015: "Invalid time period for this operation",
                -4016: "Invalid interval for kline data",
                -4017: "Invalid start time or end time",
                -4018: "Invalid limit parameter",
                -4019: "Duplicate order client ID",
                -4020: "Position cannot be modified in current state",
                -4021: "Position side cannot be changed with open orders",
                -4022: "Reduce-only order is not allowed with current position",
                -4023: "Market is closed for this symbol",
                -4024: "Symbol price filter not met",
                -4025: "Symbol lot size filter not met",
                -4026: "Symbol notional filter not met",
                -4027: "Maximum position size exceeded",
                -4028: "Maximum number of open stop orders reached",
                -4029: "Account is suspended",
                -4030: "Order would cause self-trade",
            }

            # Get suggestion for this error code
            suggestion = error_suggestions.get(error_code, "Check Binance API documentation for this error code")
            enhanced_message = f"{error_msg}. Suggestion: {suggestion}"

            # Categorize errors and raise appropriate exceptions
            if error_code in [-1121, -1013, -1014, -1015, -1016, -3008, -3013, -3014, -3015, -3016, -3017, -3018, -3019, -3020, -4013, -4024, -4025, -4026]:
                # Invalid symbol or parameter errors
                raise InvalidSymbolError(enhanced_message, error_code)
            elif error_code in [-2010, -2018, -2019, -3010, -3011, -4001, -4002, -4009]:
                # Insufficient funds or account restriction errors
                raise InsufficientFundsError(enhanced_message, error_code)
            else:
                # General Binance API errors
                raise BinanceException(enhanced_message, error_code)

        # Return the response if no error
        # At this point, response is guaranteed to be a successful response (dict[str, Any])
        # since error responses would have been caught above and raised exceptions
        return cast(dict[str, Any], response)

    # --- Public API Methods ---

    def get_server_time(self) -> ServerTimeResponse:
        """Gets the current server time.

        Returns:
            A dictionary containing the server time.
        """
        result = self._request("GET", "/api/v3/time", signed=False)
        return cast(ServerTimeResponse, result)

    def get_account_info(self) -> AccountInfo:
        """Get current account information.

        This endpoint requires authentication.

        Returns:
            An `AccountInfo` TypedDict representing the account information.
        """
        result = self._request("GET", "/api/v3/account")
        return cast(AccountInfo, result)

    def get_exchange_info(self, symbol: str | None = None, ttl_seconds: int = 3600) -> ExchangeInfo:
        """Get current exchange trading rules and symbol information.

        Caches the response to reduce latency and avoid rate-limiting.

        Args:
            symbol: The trading symbol to query (e.g., "BTCUSDT").
                If None, returns info for all symbols.
            ttl_seconds: The time-to-live for the cache entry in seconds.

        Returns:
            An `ExchangeInfo` TypedDict containing exchange information.
        """
        cache_key = f"exchange_info_{symbol.upper() if symbol else 'all'}"
        if cache_key in self._cache and time.time() < self._cache_expirations[cache_key]:
            return self._cache[cache_key]

        endpoint = "/api/v3/exchangeInfo"
        params = {"symbol": symbol.upper()} if symbol else {}
        result = self._request("GET", endpoint, params=params, signed=False)

        exchange_info = cast(ExchangeInfo, result)
        self._cache[cache_key] = exchange_info
        self._cache_expirations[cache_key] = time.time() + ttl_seconds
        return exchange_info

    def get_klines(self, symbol: str, interval: str = "1d", limit: int = 500) -> list[RawKline]:
        """Get Kline/candlestick data for a symbol.

        Klines are uniquely identified by their open time.

        Args:
            symbol: The trading symbol (e.g., "BTCUSDT").
            interval: The interval for the klines (e.g., "1m", "1h", "1d").
            limit: The number of klines to retrieve (max 1000).

        Returns:
            A list of raw kline arrays in format: [open_time, open, high, low, close, volume, ...]
        """
        endpoint = "/api/v3/klines"
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        result = self._request("GET", endpoint, params=params, signed=False)
        return cast(list[RawKline], result)

    def get_all_tickers(self) -> list[Ticker]:
        """Gets the latest price for all symbols.

        Returns:
            A list of `Ticker` TypedDicts.
        """
        result = self._request("GET", "/api/v3/ticker/price", signed=False)
        return cast(list[Ticker], result)

    def get_balances(self, min_value: float = 10.0) -> list[ProcessedBalance]:
        """Gets account balances above a minimum value threshold with USD values.

        Args:
            min_value: Minimum USD value for balances to include. Defaults to 10.

        Returns:
            A list of balance dictionaries with calculated USD values and totals.
        """
        account_info = self.get_account_info()
        tickers = {ticker["symbol"]: float(ticker["price"]) for ticker in self.get_all_tickers()}

        processed_balances: list[ProcessedBalance] = []
        for balance in account_info["balances"]:
            asset: str = balance["asset"]
            free: float = float(balance["free"])
            locked: float = float(balance["locked"])
            total: float = free + locked

            if total == 0:
                continue

            # Calculate USD value
            value_usdt: float = 0.0
            if asset == "USDT":
                value_usdt = total
            else:
                # Try different symbol combinations to find price
                usdt_symbol = f"{asset}USDT"
                busd_symbol = f"{asset}BUSD"
                btc_symbol = f"{asset}BTC"

                if usdt_symbol in tickers:
                    value_usdt = total * tickers[usdt_symbol]
                elif busd_symbol in tickers:
                    value_usdt = total * tickers[busd_symbol]
                elif btc_symbol in tickers and "BTCUSDT" in tickers:
                    btc_price: float = tickers["BTCUSDT"]
                    asset_btc_price: float = tickers[btc_symbol]
                    value_usdt = total * asset_btc_price * btc_price

            if value_usdt >= min_value:
                processed_balances.append({"asset": asset, "free": free, "locked": locked, "total": total, "value_usdt": value_usdt})

        return processed_balances

    def place_market_order(self, symbol: str, side: OrderSide, quantity: float) -> Order:
        """Places a MARKET order.

        Args:
            symbol: The trading symbol.
            side: The order side (BUY or SELL).
            quantity: The amount of the asset to trade.

        Returns:
            An `Order` TypedDict with the created order details.
        """
        params = {"symbol": symbol, "side": side.value, "type": OrderType.MARKET.value, "quantity": quantity}
        result = self._request("POST", "/api/v3/order", params=params)
        return cast(Order, result)

    def place_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float) -> Order:
        """Places a LIMIT order.

        Args:
            symbol: The trading symbol.
            side: The order side (BUY or SELL).
            quantity: The amount of the asset to trade.
            price: The price at which to execute the order.

        Returns:
            An `Order` TypedDict with the created order details.
        """
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": OrderType.LIMIT.value,
            "quantity": quantity,
            "price": price,
            "timeInForce": TimeInForce.GTC.value,
        }
        result = self._request("POST", "/api/v3/order", params=params)
        return cast(Order, result)

    def place_stop_loss_order(self, symbol: str, side: OrderSide, quantity: float, stop_price: float) -> Order:
        """Places a STOP_LOSS order.

        Args:
            symbol: The trading symbol.
            side: The order side (BUY or SELL).
            quantity: The amount of the asset to trade.
            stop_price: The price at which to trigger the stop loss.

        Returns:
            An `Order` TypedDict with the created order details.
        """
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": OrderType.STOP_LOSS.value,
            "quantity": quantity,
            "stopPrice": stop_price,
        }
        result = self._request("POST", "/api/v3/order", params=params)
        return cast(Order, result)

    def place_take_profit_order(self, symbol: str, side: OrderSide, quantity: float, stop_price: float) -> Order:
        """Places a TAKE_PROFIT order.

        Args:
            symbol: The trading symbol.
            side: The order side (BUY or SELL).
            quantity: The amount of the asset to trade.
            stop_price: The price at which to trigger the take profit.

        Returns:
            An `Order` TypedDict with the created order details.
        """
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": OrderType.TAKE_PROFIT.value,
            "quantity": quantity,
            "stopPrice": stop_price,
        }
        result = self._request("POST", "/api/v3/order", params=params)
        return cast(Order, result)

    def place_oco_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        stop_price: float,
        stop_limit_price: float | None = None,
    ) -> Order:
        """Places an OCO (One-Cancels-the-Other) order.

        This order type combines a STOP_LOSS_LIMIT and a LIMIT_MAKER order.

        Args:
            symbol: The trading symbol.
            side: The order side (BUY or SELL).
            quantity: The amount of the asset to trade.
            price: The price for the LIMIT order.
            stop_price: The trigger price for the stop loss order.
            stop_limit_price: The price for the STOP_LOSS_LIMIT
                order. If not provided, the stop
                order becomes a STOP_LOSS.

        Returns:
            An `Order` TypedDict with the created order details.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side.value,
            "quantity": quantity,
            "price": price,  # Price for the LIMIT order
            "stopPrice": stop_price,  # Price for the STOP_LOSS or STOP_LOSS_LIMIT order
            "timeInForce": TimeInForce.GTC.value,  # Required for the limit order part
        }
        # If stop_limit_price is provided, the stop order becomes a STOP_LOSS_LIMIT
        if stop_limit_price:
            params["stopLimitPrice"] = stop_limit_price
            params["stopLimitTimeInForce"] = TimeInForce.GTC.value

        result = self._request("POST", "/api/v3/order/oco", params=params)
        return cast(Order, result)

    def cancel_order(self, symbol: str, order_id: int) -> Order:
        """Cancels an active order.

        Args:
            symbol: The trading symbol of the order to cancel.
            order_id: The ID of the order to cancel.

        Returns:
            An `Order` TypedDict with the details of the canceled order.
        """
        params = {"symbol": symbol, "orderId": order_id}
        result = self._request("DELETE", "/api/v3/order", params=params)
        return cast(Order, result)

    def cancel_oco_order(self, symbol: str, order_list_id: int) -> Order:
        """Cancels an entire OCO order list.

        Args:
            symbol: The trading symbol of the OCO order to cancel.
            order_list_id: The ID of the OCO order list to cancel.

        Returns:
            An `Order` TypedDict with the details of the cancelled order list.
        """
        params = {"symbol": symbol, "orderListId": order_list_id}
        result = self._request("DELETE", "/api/v3/orderList", params=params)
        return cast(Order, result)

    def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """Gets all open orders for a symbol or all symbols.

        Args:
            symbol: The trading symbol to fetch open orders for. If None,
                fetches open orders for all symbols.

        Returns:
            A list of `Order` TypedDicts representing the open orders.
        """
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        result = self._request("GET", "/api/v3/openOrders", params=params)
        return cast(list[Order], result)

    def get_trade_history(
        self,
        symbol: str,
        limit: int = 1000,
        from_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list[Trade]:
        """Gets the trade history for a specific symbol.

        Args:
            symbol: The trading symbol.
            limit: The maximum number of trades to retrieve. Defaults to 1000.
            from_id: The ID of the trade to fetch from. If set, it will get
                trades with an ID >= from_id.
            start_time: The start time to fetch trades from (in milliseconds).
            end_time: The end time to fetch trades until (in milliseconds).

        Returns:
            A list of `Trade` TypedDicts representing the trade history.
        """
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if from_id is not None:
            params["fromId"] = from_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        result = self._request("GET", "/api/v3/myTrades", params=params)
        return cast(list[Trade], result)
