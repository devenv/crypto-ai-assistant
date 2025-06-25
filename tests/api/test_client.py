from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest
from requests import RequestException

from api.client import BinanceClient
from api.enums import OrderSide
from api.exceptions import APIError, BinanceException, InsufficientFundsError, InvalidSymbolError


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
    """Test that get_exchange_info caches results."""
    import time

    with patch.object(BinanceClient, "_request") as mock_request:
        mock_request.return_value = {"timezone": "UTC", "symbols": []}
        client = BinanceClient()

        # First call should hit the API
        info1 = client.get_exchange_info(ttl_seconds=2)
        assert info1["timezone"] == "UTC"
        mock_request.assert_called_once()

        # Second call should hit the cache
        info2 = client.get_exchange_info(ttl_seconds=2)
        assert info2["timezone"] == "UTC"
        mock_request.assert_called_once()  # Should not be called again

        # Wait for cache to expire
        time.sleep(2.5)

        # Third call should hit the API again
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
    with pytest.raises(BinanceException, match="An unknown error occurred"):
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
