# ✅ CRITICAL FIX - Use same import path as the actual code - MUST match orders.py imports
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st

from api.enums import OrderSide, OrderType
from api.exceptions import APIError
from api.models import OcoOrder, Order
from src.core.orders import OrderService


def test_order_error_handler_format_validation_error() -> None:
    """Test OrderErrorHandler formats validation errors correctly."""
    errors = ["Price too low", "Quantity invalid"]
    result = OrderErrorHandler.format_validation_error("BTCUSDT", errors)

    assert "❌ ORDER VALIDATION FAILED for BTCUSDT" in result
    assert "• Price too low" in result
    assert "• Quantity invalid" in result


def test_order_error_handler_format_parameter_error() -> None:
    """Test OrderErrorHandler formats parameter errors correctly."""
    result = OrderErrorHandler.format_parameter_error(OrderType.LIMIT, "price")

    assert result == "❌ PARAMETER ERROR: price is required for LIMIT orders"


def test_order_error_handler_format_api_error_with_details() -> None:
    """Test OrderErrorHandler formats API errors with details."""
    details = {"Error Code": "1234", "Message": "Invalid symbol"}
    result = OrderErrorHandler.format_api_error("ORDER PLACEMENT", "BTCUSDT", details)

    assert "❌ API ERROR during ORDER PLACEMENT for BTCUSDT" in result
    assert "• Error Code: 1234" in result
    assert "• Message: Invalid symbol" in result


def test_order_error_handler_format_api_error_no_details() -> None:
    """Test OrderErrorHandler formats API errors without details."""
    result = OrderErrorHandler.format_api_error("ORDER PLACEMENT", "BTCUSDT", None)

    assert result == "❌ API ERROR during ORDER PLACEMENT for BTCUSDT"
    assert "•" not in result  # No detail lines should be present


def test_order_error_handler_logging_methods() -> None:
    """Test OrderErrorHandler logging methods don't crash."""
    # These methods handle logging - just verify they don't crash
    OrderErrorHandler.log_operation_start("TEST", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0)

    test_result = {"orderId": 123, "status": "FILLED"}
    OrderErrorHandler.log_operation_success("TEST OPERATION", test_result)

    test_error = ValueError("Test error message")
    OrderErrorHandler.log_operation_failure("TEST OPERATION", test_error)


def test_order_service_get_open_orders_all() -> None:
    """Test OrderService.get_open_orders for all symbols (lines around 75)."""
    mock_client = MagicMock()
    mock_orders = [{"symbol": "BTCUSDT", "orderId": 123}]
    mock_client.get_open_orders.return_value = mock_orders

    service = OrderService(mock_client)
    result = service.get_open_orders(None)

    assert result == mock_orders
    mock_client.get_open_orders.assert_called_once_with(symbol=None)


def test_order_service_get_open_orders_specific_symbol() -> None:
    """Test OrderService.get_open_orders for specific symbol."""
    mock_client = MagicMock()
    mock_orders = [{"symbol": "ETHUSDT", "orderId": 456}]
    mock_client.get_open_orders.return_value = mock_orders

    service = OrderService(mock_client)
    result = service.get_open_orders("ETHUSDT")

    assert result == mock_orders
    mock_client.get_open_orders.assert_called_once_with(symbol="ETHUSDT")


# Import the OrderErrorHandler class
from src.core.orders import OrderErrorHandler  # noqa: E402


def test_place_oco_order_api_error_handling() -> None:
    """Test OCO order handles API errors properly."""
    mock_client = MagicMock()
    mock_precision_formatter = MagicMock()
    mock_precision_formatter.format_oco_params.return_value = ("10.00000", "2000.00", "1800.00")

    api_error = APIError("HTTP 400: Invalid OCO order")
    mock_client.place_oco_order.side_effect = api_error

    service = OrderService(mock_client)
    service._precision_formatter = mock_precision_formatter

    with pytest.raises(APIError):
        service._place_oco_order("ETHUSDT", 10.0, 2000.0, 1800.0)

    mock_client.place_oco_order.assert_called_once()


def test_place_order_exception_handling() -> None:
    """Test order placement handles various exceptions gracefully."""
    mock_client = MagicMock()
    mock_client.place_market_order.side_effect = APIError("HTTP 500: Server Error")

    with patch("src.core.orders.OrderValidator") as mock_validator_class, patch("src.core.orders.PrecisionFormatter") as mock_formatter_class:
        mock_validator = MagicMock()
        mock_validator.validate_order_placement.return_value = (True, [])
        mock_validator.get_lot_size_info_display.return_value = "📏 LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        mock_formatter = MagicMock()
        mock_formatter_class.return_value = mock_formatter

        service = OrderService(mock_client)
        service._order_validator = mock_validator
        service._precision_formatter = mock_formatter

        # Exception should be handled gracefully
        result = service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0)
        assert result is None


@patch("src.core.orders.OrderService._validate_order_request")
def test_place_order_validation_error_handling(mock_validate: MagicMock) -> None:
    """Test order placement handles validation errors."""
    mock_client = MagicMock()
    mock_validate.side_effect = ValueError("Validation failed")

    service = OrderService(mock_client)
    result = service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0)

    assert result is None


def test_place_order_unsupported_order_type(mock_client: MagicMock) -> None:
    """Test handling of unsupported order types."""
    service = OrderService(mock_client)

    fake_type = MagicMock()
    fake_type.value = "UNSUPPORTED_TYPE"

    with patch.object(service, "_validate_order_request"):
        result = service.place_order("BTCUSDT", OrderSide.BUY, fake_type, 1.0)
        assert result is None


@patch("src.core.orders.OrderService._validate_order_request")
def test_validate_order_request_success_logging(mock_validate: MagicMock) -> None:
    """Test successful validation logging (line 181)."""
    mock_client = MagicMock()
    mock_client.place_market_order.return_value = {"orderId": 123}
    mock_validate.return_value = None  # Successful validation

    service = OrderService(mock_client)

    with patch("src.core.orders.logging") as mock_logging:
        service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0)

        # Verify the success logging was called
        mock_logging.info.assert_any_call("✅ ORDER PLACEMENT SUCCESSFUL: {'orderId': 123}")


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient."""
    return MagicMock()


@pytest.fixture
def order_service(mock_client: MagicMock) -> OrderService:
    """Fixture to create an OrderService instance with a mock client."""
    with patch("src.core.orders.OrderValidator") as mock_validator_class, patch("src.core.orders.PrecisionFormatter") as mock_formatter_class:
        # Mock the validator instance
        mock_validator = MagicMock()
        # Mock BOTH validation methods that are actually called
        mock_validator.validate_order_placement.return_value = (True, [])  # ✅ CRITICAL FIX - This was missing
        mock_validator.validate_oco_order.return_value = (True, [])
        mock_validator.get_lot_size_info_display.return_value = "📏 ETHUSDT LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        # Mock the formatter instance
        mock_formatter = MagicMock()
        # Make formatters return the original values by default (pass-through)
        mock_formatter.format_oco_params.side_effect = lambda symbol, qty, price, stop: (qty, price, stop)
        mock_formatter.format_limit_params.side_effect = lambda symbol, qty, price: (qty, price)
        mock_formatter_class.return_value = mock_formatter

        service = OrderService(mock_client)
        service._order_validator = mock_validator
        service._precision_formatter = mock_formatter
        return service


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


@patch("src.core.account.AccountService")
def test_place_market_order_success(mock_account_service_cls: MagicMock, order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a MARKET order."""
    # Mock validation dependencies
    mock_client.get_all_tickers.return_value = [{"symbol": "BTCUSDT", "price": "50000.0"}]
    mock_client.get_exchange_info.return_value = {
        "symbols": [
            {
                "filters": [
                    {"filterType": "LOT_SIZE", "stepSize": "0.00001", "minQty": "0.00001", "maxQty": "999.0"},
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01", "minPrice": "0.01", "maxPrice": "1000000.0"},
                ]
            }
        ]
    }

    # Mock account service for balance validation
    mock_account_service = mock_account_service_cls.return_value
    mock_account_service.get_effective_available_balance.return_value = (10000.0, {"buy_orders": 0.0})

    # Mock successful order placement
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
    assert "❌ PARAMETER ERROR: price is required for LIMIT orders" in caplog.text

    caplog.clear()

    # Test STOP_LOSS order
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.STOP_LOSS, 0.1)
    assert order is None
    assert "❌ PARAMETER ERROR: stop_price is required for STOP_LOSS orders" in caplog.text

    caplog.clear()

    # Test TAKE_PROFIT order
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.TAKE_PROFIT, 0.1)
    assert order is None
    assert "❌ PARAMETER ERROR: stop_price is required for TAKE_PROFIT orders" in caplog.text

    caplog.clear()

    # Test OCO order
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.OCO, 0.1)
    assert order is None
    assert "❌ PARAMETER ERROR: price and stop_price is required for OCO orders" in caplog.text


def test_place_order_api_failure_returns_none(order_service: OrderService, mock_client: MagicMock, caplog: LogCaptureFixture) -> None:
    """Test that None is returned and an error is logged if the client raises an APIError."""

    import logging

    caplog.set_level(logging.ERROR)
    mock_client.place_market_order.side_effect = APIError("API Error", status_code=400)
    order = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.1)
    assert order is None
    assert "❌ ORDER PLACEMENT FAILED: APIError (HTTP 400): API Error" in caplog.text


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


def test_place_oco_order_validation_failure(mock_client: MagicMock, caplog: LogCaptureFixture) -> None:
    """Test OCO order placement when validation fails."""
    import logging

    with patch("core.orders.OrderValidator") as mock_validator_class, patch("core.orders.PrecisionFormatter") as mock_formatter_class:
        # Mock validator to return validation failure
        mock_validator = MagicMock()
        # ✅ CRITICAL FIX - Mock the method that's actually called
        mock_validator.validate_order_placement.return_value = (False, ["Order validation failed: Invalid price range"])
        mock_validator.validate_oco_order.return_value = (False, ["Invalid price range"])
        mock_validator.get_lot_size_info_display.return_value = "📏 ETHUSDT LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        mock_formatter = MagicMock()
        mock_formatter_class.return_value = mock_formatter

        service = OrderService(mock_client)
        service._order_validator = mock_validator
        service._precision_formatter = mock_formatter

        caplog.set_level(logging.ERROR)

        # Test that validation failure returns None and logs error
        result = service.place_order("ETHUSDT", OrderSide.SELL, OrderType.OCO, 1.0, price=3000, stop_price=2800)
        assert result is None
        assert "Order validation failed: Invalid price range" in caplog.text
        assert "❌ ORDER PLACEMENT FAILED: Order validation failed: Order validation failed: Invalid price range" in caplog.text


def test_place_oco_order_api_error(mock_client: MagicMock, caplog: LogCaptureFixture) -> None:
    """Test OCO order placement when API call fails."""
    import logging

    with patch("core.orders.OrderValidator") as mock_validator_class, patch("core.orders.PrecisionFormatter") as mock_formatter_class:
        # Mock successful validation and formatting
        mock_validator = MagicMock()
        # ✅ CRITICAL FIX - Mock the method that's actually called
        mock_validator.validate_order_placement.return_value = (True, [])
        mock_validator.validate_oco_order.return_value = (True, [])
        mock_validator.get_lot_size_info_display.return_value = "📏 ETHUSDT LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        mock_formatter = MagicMock()
        # Use pass-through formatting to preserve test values
        mock_formatter.format_oco_params.side_effect = lambda symbol, qty, price, stop: (qty, price, stop)
        mock_formatter_class.return_value = mock_formatter

        # Mock API error
        mock_client.place_oco_order.side_effect = APIError("API Error", 400)

        service = OrderService(mock_client)
        service._order_validator = mock_validator
        service._precision_formatter = mock_formatter

        caplog.set_level(logging.ERROR)

        # Test that API error returns None and logs detailed error
        result = service.place_order("ETHUSDT", OrderSide.SELL, OrderType.OCO, 1.0, price=3000, stop_price=2800)
        assert result is None

        # Check that detailed error logging occurred with new standardized format
        assert "❌ API ERROR during OCO ORDER PLACEMENT for ETHUSDT" in caplog.text
        assert "Symbol: ETHUSDT" in caplog.text
        assert "Formatted Quantity: 1.0" in caplog.text


def test_place_order_unsupported_type(mock_client: MagicMock, caplog: LogCaptureFixture) -> None:
    """Test placing an order with an unsupported order type."""
    import logging

    with patch("core.orders.OrderValidator") as mock_validator_class, patch("core.orders.PrecisionFormatter") as mock_formatter_class:
        mock_validator = MagicMock()
        # ✅ FIX: Mock the validate_order_placement method that's actually called
        mock_validator.validate_order_placement.return_value = (True, [])
        mock_validator.get_lot_size_info_display.return_value = "📏 Test lot size info"
        mock_validator_class.return_value = mock_validator

        mock_formatter = MagicMock()
        mock_formatter_class.return_value = mock_formatter

        service = OrderService(mock_client)
        service._order_validator = mock_validator
        service._precision_formatter = mock_formatter

        caplog.set_level(logging.ERROR)

        # Create a fake order type with a string representation
        class FakeOrderType:
            def __init__(self, value: str) -> None:
                self.value = value

        fake_order_type = FakeOrderType("FAKE_TYPE")

        result = service.place_order("BTCUSDT", OrderSide.BUY, fake_order_type, 0.1)

        assert result is None
        assert "Unsupported order type: FAKE_TYPE" in caplog.text


def test_cancel_order_missing_id_raises_error(order_service: OrderService) -> None:
    """Test that cancelling without an ID raises ValueError."""
    with pytest.raises(ValueError, match=r"❌ PARAMETER ERROR: order_id is required to cancel a standard LIMIT order"):
        order_service.cancel_order(OrderType.LIMIT, "BTCUSDT")

    with pytest.raises(ValueError, match=r"❌ PARAMETER ERROR: order_list_id is required for OCO orders"):
        order_service.cancel_order(OrderType.OCO, "ETHUSDT")


# Property-based tests using Hypothesis
@given(
    symbol=st.text(min_size=3, max_size=6, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),  # Reduced complexity
    quantity=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),  # Simpler range
    price=st.floats(min_value=100.0, max_value=500.0, allow_nan=False, allow_infinity=False),  # Narrower range
    side=st.sampled_from([OrderSide.BUY, OrderSide.SELL]),
)
@settings(max_examples=2, deadline=50, phases=[Phase.generate], suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])  # Disable shrinking
def test_place_limit_order_properties(symbol: str, quantity: float, price: float, side: OrderSide) -> None:
    """Test limit order placement properties with random parameters."""
    # Create dependencies inline to avoid fixture conflicts with Hypothesis
    mock_client = MagicMock()
    with patch("src.core.orders.OrderValidator") as mock_validator_class, patch("src.core.orders.PrecisionFormatter") as mock_formatter_class:
        # Mock the validator instance
        mock_validator = MagicMock()
        mock_validator.validate_order_placement.return_value = (True, [])
        mock_validator.get_lot_size_info_display.return_value = "📏 LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        # Mock the formatter instance
        mock_formatter = MagicMock()
        mock_formatter.format_limit_params.side_effect = lambda symbol, qty, price: (qty, price)
        mock_formatter_class.return_value = mock_formatter

        order_service = OrderService(mock_client)
        order_service._order_validator = mock_validator
        order_service._precision_formatter = mock_formatter

    # Mock successful API response
    mock_client.place_limit_order.return_value = {
        "symbol": symbol,
        "orderId": 123456,
        "side": side.value,
        "type": OrderType.LIMIT.value,
        "quantity": str(quantity),
        "price": str(price),
    }

    result = order_service.place_order(symbol, side, OrderType.LIMIT, quantity, price=price)

    # Property 1: Should return a result
    assert result is not None, "Order placement should return a result"

    # Property 2: If successful, result should be a dictionary with orderId
    if isinstance(result, dict) and "orderId" in result:
        assert result["symbol"] == symbol
        assert result["orderId"] == 123456
        assert result["side"] == side.value


@given(
    symbol=st.text(min_size=3, max_size=6, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),  # Reduced complexity
    quantity=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),  # Simpler range
    limit_price=st.floats(min_value=200.0, max_value=400.0, allow_nan=False, allow_infinity=False),  # Narrower range
    stop_price=st.floats(min_value=100.0, max_value=180.0, allow_nan=False, allow_infinity=False),  # Ensure separation
)
@settings(max_examples=2, deadline=50, phases=[Phase.generate], suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])  # Disable shrinking
def test_place_oco_order_properties(symbol: str, quantity: float, limit_price: float, stop_price: float) -> None:
    """Test OCO order placement properties with random parameters."""
    from hypothesis import assume

    # Ensure valid price separation upfront
    assume(abs(limit_price - stop_price) > 20)

    # Create dependencies inline to avoid fixture conflicts with Hypothesis
    mock_client = MagicMock()
    with patch("src.core.orders.OrderValidator") as mock_validator_class, patch("src.core.orders.PrecisionFormatter") as mock_formatter_class:
        # Mock the validator instance
        mock_validator = MagicMock()
        mock_validator.validate_order_placement.return_value = (True, [])  # Fixed method name
        mock_validator.get_lot_size_info_display.return_value = "📏 LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        # Mock the formatter instance
        mock_formatter = MagicMock()
        mock_formatter.format_oco_params.side_effect = lambda symbol, qty, price, stop: (qty, price, stop)
        mock_formatter_class.return_value = mock_formatter

        order_service = OrderService(mock_client)
        order_service._order_validator = mock_validator
        order_service._precision_formatter = mock_formatter

    # Mock successful API response
    mock_client.place_oco_order.return_value = {
        "orderListId": 789,
        "contingencyType": "OCO",
        "listStatusType": "EXEC_STARTED",
        "listOrderStatus": "EXECUTING",
        "symbol": symbol,
        "orders": [{"symbol": symbol, "orderId": 111, "clientOrderId": "limit_order"}, {"symbol": symbol, "orderId": 222, "clientOrderId": "stop_order"}],
    }

    result = order_service.place_order(symbol, OrderSide.SELL, OrderType.OCO, quantity, price=limit_price, stop_price=stop_price)

    # Property 1: Should return a result
    assert result is not None, "OCO order placement should return a result"

    # Property 2: If successful, result should be a dictionary with orderListId
    if isinstance(result, dict) and "orderListId" in result:
        assert result["symbol"] == symbol
        assert result["orderListId"] == 789
        assert "orders" in result
        assert len(result["orders"]) == 2


@given(order_list_id=st.integers(min_value=1, max_value=9999))  # Smaller range
@settings(max_examples=2, deadline=50, phases=[Phase.generate], suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])  # Disable shrinking
def test_cancel_oco_order_properties(order_list_id: int) -> None:
    """Test OCO order cancellation properties with random order list IDs."""
    # Create dependencies inline to avoid fixture conflicts with Hypothesis
    mock_client = MagicMock()
    with patch("src.core.orders.OrderValidator") as mock_validator_class, patch("src.core.orders.PrecisionFormatter") as mock_formatter_class:
        # Mock the validator instance
        mock_validator = MagicMock()
        mock_validator.validate_order_placement.return_value = (True, [])  # Fixed method name
        mock_validator.get_lot_size_info_display.return_value = "📏 LOT_SIZE: Step=0.0001, Min=0.0001"
        mock_validator_class.return_value = mock_validator

        # Mock the formatter instance
        mock_formatter = MagicMock()
        mock_formatter.format_oco_params.side_effect = lambda symbol, qty, price, stop: (qty, price, stop)
        mock_formatter_class.return_value = mock_formatter

        order_service = OrderService(mock_client)
        order_service._order_validator = mock_validator
        order_service._precision_formatter = mock_formatter

    # Mock successful cancellation response
    mock_client.cancel_oco_order.return_value = {
        "orderListId": order_list_id,
        "contingencyType": "OCO",
        "listStatusType": "ALL_DONE",
        "listOrderStatus": "ALL_DONE",
    }

    result = order_service.cancel_order(OrderType.OCO, "BTCUSDT", order_list_id=order_list_id)

    # Property: Should return cancellation result
    assert result is not None, "Order cancellation should return a result"

    # Property: Result should contain the order list ID
    if isinstance(result, dict):
        assert result.get("orderListId") == order_list_id


def test_validate_required_params_missing_parameters() -> None:
    """Test parameter validation for different order types."""
    mock_client = MagicMock()
    service = OrderService(mock_client)

    # Test LIMIT order missing price
    with pytest.raises(ValueError, match="❌ PARAMETER ERROR: price is required for LIMIT orders"):
        service._validate_required_params(OrderType.LIMIT, None, None)

    # Test STOP_LOSS order missing stop_price
    with pytest.raises(ValueError, match="❌ PARAMETER ERROR: stop_price is required for STOP_LOSS orders"):
        service._validate_required_params(OrderType.STOP_LOSS, 100.0, None)

    # Test TAKE_PROFIT order missing stop_price
    with pytest.raises(ValueError, match="❌ PARAMETER ERROR: stop_price is required for TAKE_PROFIT orders"):
        service._validate_required_params(OrderType.TAKE_PROFIT, None, None)

    # Test OCO order missing both parameters
    with pytest.raises(ValueError, match="❌ PARAMETER ERROR: price and stop_price is required for OCO orders"):
        service._validate_required_params(OrderType.OCO, None, None)
