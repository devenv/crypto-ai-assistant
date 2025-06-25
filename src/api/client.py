import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from api.enums import OrderSide, OrderType, TimeInForce
from api.exceptions import APIError, BinanceException, InsufficientFundsError, InvalidSymbolError
from api.models import AccountInfo, ExchangeInfo, Kline, Order, Ticker, Trade

# Configure logging
logger = logging.getLogger(__name__)


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
        self._cache: Dict[str, ExchangeInfo] = {}
        self._cache_expirations: Dict[str, float] = {}

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

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, signed: bool = True) -> Any:
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
            response = self.session.request(
                method=method.upper(),
                url=f"{self.base_url}{endpoint}",
                params=request_params if method.upper() in ["GET", "DELETE"] else None,
                data=request_params if method.upper() == "POST" else None,
            )
            response.raise_for_status()
            # Cast the result to the expected union type to satisfy mypy
            json_response = response.json()
            return self._handle_response(json_response)
        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response else None
            raise APIError(str(e), status_code=status_code) from e

    def _handle_response(self, response: Any) -> Any:
        """Handles the Binance API response, checking for errors.

        Args:
            response: The response from the API.

        Returns:
            The response if no error is found.

        Raises:
            InvalidSymbolError: If the symbol in the request is not valid.
            InsufficientFundsError: If the account has insufficient funds for the request.
            BinanceException: For other Binance API errors.
        """
        if isinstance(response, dict) and "code" in response:
            code = int(response["code"])
            # Error codes are negative
            if code < 0:
                msg = response.get("msg", "An unknown error occurred.")
                if code == -1121:
                    raise InvalidSymbolError(message=msg, code=code)
                if code == -2010 and "insufficient balance" in msg.lower():
                    raise InsufficientFundsError(message=msg, code=code)
                raise BinanceException(message=msg, code=code)
        return response

    # --- Public API Methods ---

    def get_server_time(self) -> Dict[str, Any]:
        """Gets the current server time.

        Returns:
            A dictionary containing the server time.
        """
        result = self._request("GET", "/api/v3/time", signed=False)
        return cast(Dict[str, Any], result)

    def get_account_info(self) -> AccountInfo:
        """Get current account information.

        This endpoint requires authentication.

        Returns:
            An `AccountInfo` TypedDict representing the account information.
        """
        result = self._request("GET", "/api/v3/account")
        return cast(AccountInfo, result)

    def get_exchange_info(self, symbol: Optional[str] = None, ttl_seconds: int = 3600) -> ExchangeInfo:
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

    def get_klines(self, symbol: str, interval: str = "1d", limit: int = 500) -> List[Kline]:
        """Get Kline/candlestick data for a symbol.

        Klines are uniquely identified by their open time.

        Args:
            symbol: The trading symbol (e.g., "BTCUSDT").
            interval: The interval for the klines (e.g., "1m", "1h", "1d").
            limit: The number of klines to retrieve (max 1000).

        Returns:
            A list of `Kline` TypedDicts.
        """
        endpoint = "/api/v3/klines"
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        result = self._request("GET", endpoint, params=params, signed=False)
        return cast(List[Kline], result)

    def get_all_tickers(self) -> List[Ticker]:
        """Gets the latest price for all symbols.

        Returns:
            A list of `Ticker` TypedDicts.
        """
        result = self._request("GET", "/api/v3/ticker/price", signed=False)
        return cast(List[Ticker], result)

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
        stop_limit_price: Optional[float] = None,
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
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.value,
            "quantity": quantity,
            "price": price,  # Price for the LIMIT order
            "stopPrice": stop_price,  # Price for the STOP_LOSS or STOP_LOSS_LIMIT order
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

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Gets all open orders for a symbol or all symbols.

        Args:
            symbol: The trading symbol to fetch open orders for. If None,
                fetches open orders for all symbols.

        Returns:
            A list of `Order` TypedDicts representing the open orders.
        """
        params: Dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        result = self._request("GET", "/api/v3/openOrders", params=params)
        return cast(List[Order], result)

    def get_trade_history(
        self,
        symbol: str,
        limit: int = 1000,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Trade]:
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
        params: Dict[str, Any] = {"symbol": symbol, "limit": limit}
        if from_id is not None:
            params["fromId"] = from_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        result = self._request("GET", "/api/v3/myTrades", params=params)
        return cast(List[Trade], result)
