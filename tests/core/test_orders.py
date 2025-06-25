from typing import cast
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture

from api.enums import OrderSide, OrderType
from api.exceptions import APIError
from api.models import OcoOrder, Order
from core.orders import OrderService


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient."""
    return MagicMock()


@pytest.fixture
def order_service(mock_client: MagicMock) -> OrderService:
    """Fixture to create an OrderService instance with a mock client."""
    return OrderService(mock_client)


def test_get_open_orders_with_symbol(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test fetching open orders for a specific symbol."""
    mock_order_data = [{"symbol": "BTCUSDT", "orderId": 1}]
    mock_client.get_open_orders.return_value = mock_order_data

    orders = order_service.get_open_orders(symbol="BTCUSDT")

    assert len(orders) == 1
    assert orders == mock_order_data
    mock_client.get_open_orders.assert_called_once_with(symbol="BTCUSDT")


def test_get_open_orders_all_symbols(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test fetching open orders for all symbols."""
    mock_order_data = [{"symbol": "BTCUSDT", "orderId": 1}]
    mock_client.get_open_orders.return_value = mock_order_data

    orders = order_service.get_open_orders(symbol=None)

    assert len(orders) == 1
    assert orders == mock_order_data
    mock_client.get_open_orders.assert_called_once_with(symbol=None)


def test_get_open_orders_no_orders(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test handling of no open orders."""
    mock_client.get_open_orders.return_value = []

    orders = order_service.get_open_orders(symbol="BTCUSDT")

    assert len(orders) == 0
    mock_client.get_open_orders.assert_called_once_with(symbol="BTCUSDT")


# --- Tests for place_order ---


def test_place_limit_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a LIMIT order."""
    mock_client.place_limit_order.return_value = {"symbol": "BTCUSDT", "orderId": 123}
    order_result = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 0.1, price=50000)
    assert order_result is not None
    order = cast(Order, order_result)
    assert order["orderId"] == 123
    mock_client.place_limit_order.assert_called_once_with(symbol="BTCUSDT", side=OrderSide.BUY, quantity=0.1, price=50000)


def test_place_market_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a MARKET order."""
    mock_client.place_market_order.return_value = {"symbol": "BTCUSDT", "orderId": 124}
    order_result = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.1)
    assert order_result is not None
    order = cast(Order, order_result)
    assert order["orderId"] == 124
    mock_client.place_market_order.assert_called_once_with(symbol="BTCUSDT", side=OrderSide.BUY, quantity=0.1)


def test_place_stop_loss_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a STOP_LOSS order."""
    mock_client.place_stop_loss_order.return_value = {"symbol": "BTCUSDT", "orderId": 125}
    order_result = order_service.place_order("BTCUSDT", OrderSide.SELL, OrderType.STOP_LOSS, 0.1, stop_price=45000)
    assert order_result is not None
    order = cast(Order, order_result)
    assert order["orderId"] == 125
    mock_client.place_stop_loss_order.assert_called_once_with(symbol="BTCUSDT", side=OrderSide.SELL, quantity=0.1, stop_price=45000)


def test_place_take_profit_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a TAKE_PROFIT order."""
    mock_client.place_take_profit_order.return_value = {"symbol": "BTCUSDT", "orderId": 126}
    order_result = order_service.place_order("BTCUSDT", OrderSide.SELL, OrderType.TAKE_PROFIT, 0.1, stop_price=55000)
    assert order_result is not None
    order = cast(Order, order_result)
    assert order["orderId"] == 126
    mock_client.place_take_profit_order.assert_called_once_with(symbol="BTCUSDT", side=OrderSide.SELL, quantity=0.1, stop_price=55000)


def test_place_oco_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a SELL OCO order."""
    mock_client.place_oco_order.return_value = {"orderListId": 1, "orders": []}
    order_result = order_service.place_order("ETHUSDT", OrderSide.SELL, OrderType.OCO, 1.0, price=3000, stop_price=2800)
    assert order_result is not None
    order = cast(OcoOrder, order_result)
    assert order["orderListId"] == 1
    mock_client.place_oco_order.assert_called_once()


def test_place_order_returns_none_for_missing_params(order_service: OrderService, caplog: LogCaptureFixture) -> None:
    """Test that placing orders with missing required parameters returns None and logs an error."""
    import logging

    caplog.set_level(logging.ERROR)

    # Test LIMIT order
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 0.1)
    assert order is None
    assert "Price is required for LIMIT orders." in caplog.text
    caplog.clear()

    # Test STOP_LOSS order
    order = order_service.place_order("BTCUSDT", OrderSide.SELL, OrderType.STOP_LOSS, 0.1)
    assert order is None
    assert "Stop price is required for STOP_LOSS orders." in caplog.text
    caplog.clear()

    # Test TAKE_PROFIT order
    order = order_service.place_order("BTCUSDT", OrderSide.SELL, OrderType.TAKE_PROFIT, 0.1)
    assert order is None
    assert "Stop price is required for TAKE_PROFIT orders." in caplog.text
    caplog.clear()

    # Test OCO order
    order = order_service.place_order("ETHUSDT", OrderSide.SELL, OrderType.OCO, 1.0, price=3000)
    assert order is None
    assert "Price and stop_price are required for OCO orders." in caplog.text


def test_place_order_api_failure_returns_none(order_service: OrderService, mock_client: MagicMock, caplog: LogCaptureFixture) -> None:
    """Test that None is returned and an error is logged if the client raises an APIError."""
    import logging

    caplog.set_level(logging.ERROR)
    mock_client.place_market_order.side_effect = APIError("API Error", status_code=400)
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.1)
    assert order is None
    assert "Failed to place order: APIError (HTTP 400): API Error" in caplog.text


def test_place_unsupported_order_type(order_service: OrderService, caplog: LogCaptureFixture) -> None:
    """Test that an unsupported order type is logged and returns None."""
    import logging

    caplog.set_level(logging.ERROR)
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, "INVALID_TYPE", 1.0)  # type: ignore
    assert order is None
    assert "Unsupported order type: INVALID_TYPE" in caplog.text


def test_place_order_with_unhandled_valid_type(order_service: OrderService, caplog: LogCaptureFixture) -> None:
    """Test that a valid but unhandled OrderType returns None and logs an error."""
    import logging

    caplog.set_level(logging.ERROR)
    # Use an OrderType that is valid but not handled by the if/elif chain in place_order
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.LIMIT_MAKER, 1.0)
    assert order is None
    assert "Unsupported order type: LIMIT_MAKER" in caplog.text


# --- Tests for cancel_order ---


def test_cancel_standard_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful cancellation of a standard order."""
    mock_client.cancel_order.return_value = {"symbol": "BTCUSDT", "orderId": 123}
    result_val = order_service.cancel_order(OrderType.LIMIT, "BTCUSDT", order_id=123)
    assert result_val is not None
    result = cast(Order, result_val)
    assert result["orderId"] == 123
    mock_client.cancel_order.assert_called_once_with(symbol="BTCUSDT", order_id=123)


def test_cancel_oco_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful cancellation of an OCO order."""
    mock_client.cancel_oco_order.return_value = {"orderListId": 2}
    result_val = order_service.cancel_order(OrderType.OCO, "ETHUSDT", order_list_id=2)
    assert result_val is not None
    result = cast(OcoOrder, result_val)
    assert result["orderListId"] == 2
    mock_client.cancel_oco_order.assert_called_once_with(symbol="ETHUSDT", order_list_id=2)


def test_cancel_order_missing_id_raises_error(order_service: OrderService) -> None:
    """Test that cancelling without an ID raises ValueError."""
    with pytest.raises(ValueError, match="order_id is required to cancel a standard order."):
        order_service.cancel_order(OrderType.LIMIT, "BTCUSDT")

    with pytest.raises(ValueError, match="order_list_id is required to cancel OCO orders."):
        order_service.cancel_order(OrderType.OCO, "ETHUSDT")
