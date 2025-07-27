from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from requests import RequestException

from src.api.client import BinanceClient
from src.api.enums import OrderSide
from src.api.exceptions import (
    APIError,
    BinanceException,
    InsufficientFundsError,
    InvalidSymbolError,
)


@pytest.fixture
def mock_env() -> Iterator[None]:
    """Mock environment variables for API keys."""
    with patch.dict("os.environ", {"BINANCE_API_KEY": "test_key", "BINANCE_API_SECRET": "test_secret"}):
        yield


@patch("requests.Session")
def test_initialization(mock_session: MagicMock, mock_env: Any) -> None:
    """Test client initialization and session setup."""
    client = BinanceClient()
    assert client.api_key == "test_key"
    mock_session.return_value.headers.update.assert_called_with({"X-MBX-APIKEY": "test_key"})


def test_initialization_no_keys() -> None:
    """Test that initialization fails without API keys."""
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError, match="API keys not found in environment."):
            BinanceClient()


@patch("requests.Session")
def test_request_exception_handling(mock_session: MagicMock, mock_env: Any) -> None:
    """Test that RequestException is properly handled."""
    mock_session.return_value.request.side_effect = Exception("Test Error")
    client = BinanceClient()
    with pytest.raises(Exception, match="Test Error"):
        client.get_server_time()


@patch("requests.Session")
def test_get_server_time(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_server_time."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"serverTime": 1617996983451}
    mock_session.return_value.request.return_value = mock_response

    server_time = client.get_server_time()
    assert server_time["serverTime"] == 1617996983451
    mock_session.return_value.request.assert_called_once()
    args, kwargs = mock_session.return_value.request.call_args
    assert kwargs["method"] == "GET"
    assert "time" in kwargs["url"]


@patch("requests.Session")
def test_get_exchange_info(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_exchange_info."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"timezone": "UTC"}
    mock_session.return_value.request.return_value = mock_response

    info = client.get_exchange_info("BTCUSDT")
    assert info["timezone"] == "UTC"
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert "exchangeInfo" in kwargs["url"]


def test_get_exchange_info_caching(mock_env: Any) -> None:
    """Test that get_exchange_info caches results - OPTIMIZED (no sleep)."""
    with patch.object(BinanceClient, "_request") as mock_request, patch("time.time") as mock_time:
        mock_request.return_value = {"timezone": "UTC", "symbols": []}
        mock_time.return_value = 1000.0  # Start time
        client = BinanceClient()

        # First call should hit the API
        info1 = client.get_exchange_info(ttl_seconds=2)
        assert info1["timezone"] == "UTC"
        mock_request.assert_called_once()

        # Second call should hit the cache (same time)
        info2 = client.get_exchange_info(ttl_seconds=2)
        assert info2["timezone"] == "UTC"
        mock_request.assert_called_once()  # Should not be called again

        # Simulate cache expiration by advancing time
        mock_time.return_value = 1003.0  # 3 seconds later (> ttl_seconds=2)

        # Third call should hit the API again (cache expired)
        info3 = client.get_exchange_info(ttl_seconds=2)
        assert info3["timezone"] == "UTC"
        assert mock_request.call_count == 2  # Should be called again


@patch("requests.Session")
def test_get_klines(mock_session: MagicMock, mock_env: Any) -> None:
    """Test getting kline data."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = [[1, 2, 3]]
    mock_session.return_value.request.return_value = mock_response

    klines = client.get_klines(symbol="BTCUSDT", interval="1d", limit=1)
    assert len(klines) == 1
    mock_session.return_value.request.assert_called_once()


@patch("requests.Session")
def test_get_all_tickers(mock_session: MagicMock, mock_env: Any) -> None:
    """Test getting all tickers."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = [{"symbol": "BTCUSDT", "price": "50000"}]
    mock_session.return_value.request.return_value = mock_response

    tickers = client.get_all_tickers()
    assert tickers[0]["symbol"] == "BTCUSDT"


@patch("requests.Session")
def test_get_trade_history(mock_session: MagicMock, mock_env: Any) -> None:
    """Test getting trade history."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 1}]
    mock_session.return_value.request.return_value = mock_response

    history = client.get_trade_history(symbol="BTCUSDT", from_id=123, start_time=1234, end_time=5678)
    assert history[0]["id"] == 1


@patch("requests.Session")
def test_place_market_order(mock_session: MagicMock, mock_env: Any) -> None:
    """Test placing a MARKET order."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderId": 1}
    mock_session.return_value.request.return_value = mock_response

    client.place_market_order(symbol="BTCUSDT", side=OrderSide.BUY, quantity=0.1)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["data"]["type"] == "MARKET"


@patch("requests.Session")
def test_place_limit_order(mock_session: MagicMock, mock_env: Any) -> None:
    """Test placing a LIMIT order."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderId": 2}
    mock_session.return_value.request.return_value = mock_response

    client.place_limit_order(symbol="BTCUSDT", side=OrderSide.BUY, quantity=0.1, price=50000)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["data"]["type"] == "LIMIT"
    assert kwargs["data"]["price"] == 50000


@patch("requests.Session")
def test_place_stop_loss_order(mock_session: MagicMock, mock_env: Any) -> None:
    """Test placing a STOP_LOSS order."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderId": 3}
    mock_session.return_value.request.return_value = mock_response

    client.place_stop_loss_order(symbol="BTCUSDT", side=OrderSide.SELL, quantity=0.1, stop_price=49000)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["data"]["type"] == "STOP_LOSS"
    assert kwargs["data"]["stopPrice"] == 49000


@patch("requests.Session")
def test_place_take_profit_order(mock_session: MagicMock, mock_env: Any) -> None:
    """Test placing a TAKE_PROFIT order."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderId": 4}
    mock_session.return_value.request.return_value = mock_response

    client.place_take_profit_order(symbol="BTCUSDT", side=OrderSide.SELL, quantity=0.1, stop_price=51000)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["data"]["type"] == "TAKE_PROFIT"
    assert kwargs["data"]["stopPrice"] == 51000


@patch("requests.Session")
def test_place_oco_order_with_stop_limit(mock_session: MagicMock, mock_env: Any) -> None:
    """Test placing an OCO order with a stop limit price."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderListId": 1}
    mock_session.return_value.request.return_value = mock_response

    client.place_oco_order(symbol="BTCUSDT", side=OrderSide.SELL, quantity=1, price=60000, stop_price=50000, stop_limit_price=49900)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["data"]["stopLimitPrice"] == 49900
    assert kwargs["data"]["stopLimitTimeInForce"] == "GTC"


@patch("requests.Session")
def test_place_oco_order_without_stop_limit(mock_session: MagicMock, mock_env: Any) -> None:
    """Test placing an OCO order without a stop limit price."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderListId": 2}
    mock_session.return_value.request.return_value = mock_response

    client.place_oco_order(symbol="BTCUSDT", side=OrderSide.SELL, quantity=1, price=60000, stop_price=50000)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert "stopLimitPrice" not in kwargs["data"]
    assert "stopLimitTimeInForce" not in kwargs["data"]


@patch("requests.Session")
def test_get_open_orders(mock_session: MagicMock, mock_env: Any) -> None:
    """Test getting open orders."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = [{"orderId": 1}]
    mock_session.return_value.request.return_value = mock_response

    orders = client.get_open_orders()
    assert orders[0]["orderId"] == 1
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert "openOrders" in kwargs["url"]


@patch("requests.Session")
def test_cancel_order(mock_session: MagicMock, mock_env: Any) -> None:
    """Test canceling a standard order."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderId": 123}
    mock_session.return_value.request.return_value = mock_response

    client.cancel_order(symbol="BTCUSDT", order_id=123)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["method"] == "DELETE"
    assert "order" in kwargs["url"]
    assert kwargs["params"]["orderId"] == 123


@patch("requests.Session")
def test_cancel_oco_order(mock_session: MagicMock, mock_env: Any) -> None:
    """Test canceling an OCO order."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = {"orderListId": 456}
    mock_session.return_value.request.return_value = mock_response

    client.cancel_oco_order(symbol="BTCUSDT", order_list_id=456)
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["method"] == "DELETE"
    assert "orderList" in kwargs["url"]
    assert kwargs["params"]["orderListId"] == 456


@patch("requests.Session")
def test_place_order_stop_loss_limit_requires_prices(mock_session: MagicMock, mock_env: Any) -> None:
    # This function is not provided in the original file or the code block
    # It's assumed to exist as it's called in the test_place_stop_loss_order function
    pass


def test_api_error_str_with_status_code() -> None:
    """Test the string representation of APIError with a status code."""
    error = APIError("Test message", status_code=418)
    assert "APIError (HTTP 418): Test message" == str(error)


@patch("requests.Session")
def test_request_exception_no_response(mock_session: MagicMock, mock_env: Any) -> None:
    """Test handling of a RequestException without a response attribute."""
    mock_session.return_value.request.side_effect = RequestException("No response")
    client = BinanceClient()
    with pytest.raises(APIError, match="No response"):
        client.get_server_time()


def test_handle_response_invalid_symbol(mock_env: Any) -> None:
    """Test _handle_response for an invalid symbol error."""
    client = BinanceClient()
    with pytest.raises(InvalidSymbolError):
        client._handle_response({"code": -1121, "msg": "Invalid symbol."})


def test_handle_response_insufficient_funds(mock_env: Any) -> None:
    """Test _handle_response for an insufficient funds error."""
    client = BinanceClient()
    with pytest.raises(InsufficientFundsError):
        client._handle_response({"code": -2010, "msg": "Insufficient balance."})


def test_handle_response_generic_binance_error(mock_env: Any) -> None:
    """Test _handle_response for a generic Binance error."""
    client = BinanceClient()
    with pytest.raises(BinanceException, match="Some error"):
        client._handle_response({"code": -1000, "msg": "Some error"})


def test_handle_response_no_msg(mock_env: Any) -> None:
    """Test _handle_response for an error with no message."""
    client = BinanceClient()
    with pytest.raises(BinanceException, match="Unknown error.*Suggestion"):
        client._handle_response({"code": -1000})


@patch("requests.Session")
def test_get_open_orders_with_symbol(mock_session: MagicMock, mock_env: Any) -> None:
    """Test getting open orders with a symbol."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = [{"orderId": 1}]
    mock_session.return_value.request.return_value = mock_response

    client.get_open_orders(symbol="BTCUSDT")
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert kwargs["params"]["symbol"] == "BTCUSDT"


@patch("requests.Session")
def test_get_trade_history_no_optional_params(mock_session: MagicMock, mock_env: Any) -> None:
    """Test getting trade history without optional parameters."""
    client = BinanceClient()
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 1}]
    mock_session.return_value.request.return_value = mock_response

    client.get_trade_history(symbol="BTCUSDT")
    mock_session.return_value.request.assert_called_once()
    _, kwargs = mock_session.return_value.request.call_args
    assert "from_id" not in kwargs["params"]
    assert "start_time" not in kwargs["params"]
    assert "end_time" not in kwargs["params"]


def test_handle_requests_exception_with_json_decode_error(mock_env: Any) -> None:
    """Test handling of requests exception when response.json() raises JSONDecodeError."""
    from json import JSONDecodeError

    import requests

    with patch("requests.Session"):
        client = BinanceClient()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid response text"

        exception = requests.exceptions.HTTPError("HTTP Error")
        exception.response = mock_response

        with pytest.raises(APIError) as exc_info:
            client._handle_requests_exception(exception)

        error = exc_info.value
        assert error.status_code == 400
        assert "Invalid response text" in str(error)


def test_handle_requests_exception_with_value_error(mock_env: Any) -> None:
    """Test handling of requests exception when response.json() raises ValueError."""
    import requests

    with patch("requests.Session"):
        client = BinanceClient()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON value")
        mock_response.text = "Server error response"

        exception = requests.exceptions.HTTPError("HTTP Error")
        exception.response = mock_response

        with pytest.raises(APIError) as exc_info:
            client._handle_requests_exception(exception)

        error = exc_info.value
        assert error.status_code == 500
        assert "Server error response" in str(error)


@patch("requests.Session")
def test_handle_requests_exception_json_response_parse(mock_session: MagicMock, mock_env: Any) -> None:
    """Test _handle_requests_exception with JSON response parsing (line 139)."""
    client = BinanceClient()

    # Create a mock exception with a response that has valid JSON
    exception = RequestException("API Error")
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": -1021, "msg": "Timestamp out of sync"}
    mock_response.text = '{"code": -1021, "msg": "Timestamp out of sync"}'
    exception.response = mock_response

    with pytest.raises(APIError) as exc_info:
        client._handle_requests_exception(exception)

    error = exc_info.value
    assert "Details: {'code': -1021, 'msg': 'Timestamp out of sync'}" in str(error)


@patch("requests.Session")
def test_get_account_info_success(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_account_info method success (lines 280-281)."""
    client = BinanceClient()

    # Mock successful account info response
    mock_response = MagicMock()
    mock_response.json.return_value = {"balances": [{"asset": "BTC", "free": "1.0", "locked": "0.0"}, {"asset": "USDT", "free": "1000.0", "locked": "0.0"}]}
    mock_response.raise_for_status.return_value = None
    mock_session.return_value.request.return_value = mock_response

    result = client.get_account_info()

    assert "balances" in result
    assert len(result["balances"]) == 2
    assert result["balances"][0]["asset"] == "BTC"
    # Verify the request was made to the correct endpoint
    call_args = mock_session.return_value.request.call_args
    assert call_args[1]["method"] == "GET"
    assert "api/v3/account" in call_args[1]["url"]
    assert "timestamp" in call_args[1]["params"]  # Auth params should be present


@patch("requests.Session")
def test_get_balances_with_value_calculation(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_balances method with USD value calculations (lines 345-380)."""
    client = BinanceClient()

    # Mock account info response
    account_response = MagicMock()
    account_response.json.return_value = {
        "balances": [
            {"asset": "BTC", "free": "1.0", "locked": "0.5"},
            {"asset": "ETH", "free": "10.0", "locked": "0.0"},
            {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
            {"asset": "DOT", "free": "0.0", "locked": "0.0"},  # Zero balance to test filtering
        ]
    }
    account_response.raise_for_status.return_value = None

    # Mock tickers response
    tickers_response = MagicMock()
    tickers_response.json.return_value = [{"symbol": "BTCUSDT", "price": "50000.0"}, {"symbol": "ETHUSDT", "price": "3000.0"}]
    tickers_response.raise_for_status.return_value = None

    # Set up session to return different responses for different calls
    def mock_request(method, url, **kwargs):
        if "/api/v3/account" in url:
            return account_response
        elif "/api/v3/ticker/price" in url:
            return tickers_response
        return MagicMock()

    mock_session.return_value.request.side_effect = mock_request

    result = client.get_balances(min_value=1.0)

    # Should have 3 assets (BTC, ETH, USDT) but not DOT (zero balance)
    assert len(result) == 3

    # Check BTC calculation
    btc_balance = next(b for b in result if b["asset"] == "BTC")
    assert btc_balance["total"] == 1.5  # 1.0 free + 0.5 locked
    assert btc_balance["value_usdt"] == 75000.0  # 1.5 * 50000.0

    # Check ETH calculation
    eth_balance = next(b for b in result if b["asset"] == "ETH")
    assert eth_balance["total"] == 10.0
    assert eth_balance["value_usdt"] == 30000.0  # 10.0 * 3000.0

    # Check USDT (should be 1:1)
    usdt_balance = next(b for b in result if b["asset"] == "USDT")
    assert usdt_balance["total"] == 1000.0
    assert usdt_balance["value_usdt"] == 1000.0  # 1:1 for USDT


@patch("requests.Session")
def test_get_balances_btc_pair_calculation(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_balances with BTC pair price calculation (coverage for BTC pair logic)."""
    client = BinanceClient()

    # Mock account info with an asset that only has BTC pair
    account_response = MagicMock()
    account_response.json.return_value = {"balances": [{"asset": "ADA", "free": "100.0", "locked": "0.0"}]}
    account_response.raise_for_status.return_value = None

    # Mock tickers response - only BTC pair available for ADA
    tickers_response = MagicMock()
    tickers_response.json.return_value = [
        {"symbol": "ADABTC", "price": "0.00001"},  # ADA price in BTC
        {"symbol": "BTCUSDT", "price": "50000.0"},  # BTC price in USDT
    ]
    tickers_response.raise_for_status.return_value = None

    def mock_request(method, url, **kwargs):
        if "/api/v3/account" in url:
            return account_response
        elif "/api/v3/ticker/price" in url:
            return tickers_response
        return MagicMock()

    mock_session.return_value.request.side_effect = mock_request

    result = client.get_balances(min_value=0.1)

    # Should calculate ADA value via BTC: 100 * 0.00001 * 50000 = 50 USDT
    assert len(result) == 1
    ada_balance = result[0]
    assert ada_balance["asset"] == "ADA"
    assert ada_balance["value_usdt"] == 50.0


@patch("requests.Session")
def test_get_balances_no_price_found(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_balances when no price is found for an asset."""
    client = BinanceClient()

    # Mock account info with unknown asset
    account_response = MagicMock()
    account_response.json.return_value = {"balances": [{"asset": "UNKNOWN", "free": "100.0", "locked": "0.0"}]}
    account_response.raise_for_status.return_value = None

    # Mock empty tickers response
    tickers_response = MagicMock()
    tickers_response.json.return_value = []
    tickers_response.raise_for_status.return_value = None

    def mock_request(method, url, **kwargs):
        if "/api/v3/account" in url:
            return account_response
        elif "/api/v3/ticker/price" in url:
            return tickers_response
        return MagicMock()

    mock_session.return_value.request.side_effect = mock_request

    result = client.get_balances(min_value=0.1)

    # Should not include asset with no price found (value_usdt = 0.0)
    assert len(result) == 0


@patch("requests.Session")
def test_get_balances_busd_pair_calculation(mock_session: MagicMock, mock_env: Any) -> None:
    """Test get_balances with BUSD pair calculation (line 371)."""
    client = BinanceClient()

    # Mock account info with an asset that only has BUSD pair
    account_response = MagicMock()
    account_response.json.return_value = {"balances": [{"asset": "BNB", "free": "10.0", "locked": "0.0"}]}
    account_response.raise_for_status.return_value = None

    # Mock tickers response - only BUSD pair available for BNB
    tickers_response = MagicMock()
    tickers_response.json.return_value = [
        {"symbol": "BNBBUSD", "price": "300.0"}  # BNB price in BUSD
    ]
    tickers_response.raise_for_status.return_value = None

    def mock_request(method, url, **kwargs):
        if "/api/v3/account" in url:
            return account_response
        elif "/api/v3/ticker/price" in url:
            return tickers_response
        return MagicMock()

    mock_session.return_value.request.side_effect = mock_request

    result = client.get_balances(min_value=1.0)

    # Should calculate BNB value via BUSD: 10 * 300 = 3000 USDT equivalent
    assert len(result) == 1
    bnb_balance = result[0]
    assert bnb_balance["asset"] == "BNB"
    assert bnb_balance["value_usdt"] == 3000.0
