"""Order Management Module.

This module provides services for placing, managing, and validating
cryptocurrency trading orders through the Binance API.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from api.client import BinanceClient
from api.enums import OrderSide, OrderType
from api.exceptions import APIError
from api.models import OcoOrder, Order

from .order_validator import OrderValidator
from .precision_formatter import PrecisionFormatter


class OrderErrorHandler:
    """Standardized error handling for order operations with consistent formatting."""

    @staticmethod
    def format_validation_error(symbol: str, errors: list[str]) -> str:
        """Format validation errors with consistent structure."""
        error_header = f"❌ ORDER VALIDATION FAILED for {symbol}"
        error_details = "\n".join(f"  • {error}" for error in errors)
        return f"{error_header}:\n{error_details}"

    @staticmethod
    def format_parameter_error(order_type: OrderType, missing_param: str) -> str:
        """Format parameter validation errors consistently."""
        return f"❌ PARAMETER ERROR: {missing_param} is required for {order_type.value} orders"

    @staticmethod
    def format_api_error(operation: str, symbol: str, details: dict[str, Any] | None = None) -> str:
        """Format API errors with structured details."""
        header = f"❌ API ERROR during {operation} for {symbol}"
        if details:
            detail_lines = [f"  • {key}: {value}" for key, value in details.items()]
            return f"{header}:\n" + "\n".join(detail_lines)
        return header

    @staticmethod
    def log_operation_start(operation: str, symbol: str, side: OrderSide, order_type: OrderType | Any, quantity: float) -> None:
        """Log operation start with consistent format."""
        # Handle both valid OrderType enums and invalid types gracefully
        order_type_display = getattr(order_type, "value", str(order_type))
        side_display = getattr(side, "value", str(side))
        logging.info(f"🔍 STARTING {operation.upper()}: {side_display} {order_type_display} order for {quantity} {symbol}")

    @staticmethod
    def log_operation_success(operation: str, result: Any) -> None:
        """Log successful operations consistently."""
        logging.info(f"✅ {operation.upper()} SUCCESSFUL: {result}")

    @staticmethod
    def log_operation_failure(operation: str, error: Exception) -> None:
        """Log operation failures consistently."""
        logging.error(f"❌ {operation.upper()} FAILED: {error}")


class OrderService:
    """Provides methods for placing and managing orders."""

    def __init__(self, client: BinanceClient) -> None:
        """Initializes the OrderService.

        Args:
            client: An instance of `BinanceClient` to interact with the API.
        """
        self._client = client
        self._precision_formatter = PrecisionFormatter(client)
        self._order_validator = OrderValidator(client)

    def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """Fetches open orders for a specific symbol or all symbols.

        Args:
            symbol: The trading symbol to fetch open orders for. If None,
                fetches open orders for all symbols.

        Returns:
            A list of `Order` TypedDicts representing the open orders.
        """
        result = self._client.get_open_orders(symbol=symbol)
        return cast(list[Order], result)

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
    ) -> Order | OcoOrder | None:
        """Places an order by routing to the correct client method based on order type.

        This method centralizes order placement logic, validating inputs and
        calling the appropriate `BinanceClient` method for the given order type.

        Args:
            symbol: The trading symbol.
            side: The order side (BUY or SELL).
            order_type: The type of order to place.
            quantity: The amount of the asset to trade.
            price: The price for LIMIT or OCO orders.
            stop_price: The trigger price for STOP_LOSS or TAKE_PROFIT orders.

        Returns:
            An `Order` TypedDict with the created order details, or None if
            the order placement fails.

        Raises:
            ValueError: If a required parameter for a specific order type is missing.
        """
        try:
            # 🚨 CRITICAL: Pre-flight validation to prevent immediate fills and other errors
            OrderErrorHandler.log_operation_start("ORDER PLACEMENT", symbol, side, order_type, quantity)

            self._validate_order_request(symbol, side, order_type, quantity, price, stop_price)

            order: Order | OcoOrder | None = None
            if order_type == OrderType.MARKET:
                order = self._place_market_order(symbol, side, quantity)
            elif order_type == OrderType.LIMIT:
                self._validate_required_params(order_type, price, None)
                assert price is not None  # Type assertion after validation
                order = self._place_limit_order(symbol, side, quantity, price)
            elif order_type == OrderType.STOP_LOSS:
                self._validate_required_params(order_type, None, stop_price)
                assert stop_price is not None  # Type assertion after validation
                order = self._place_stop_loss_order(symbol, side, quantity, stop_price)
            elif order_type == OrderType.TAKE_PROFIT:
                self._validate_required_params(order_type, None, stop_price)
                assert stop_price is not None  # Type assertion after validation
                order = self._place_take_profit_order(symbol, side, quantity, stop_price)
            elif order_type == OrderType.OCO:
                self._validate_required_params(order_type, price, stop_price)
                assert price is not None and stop_price is not None  # Type assertion after validation
                order = self._place_oco_order(symbol, quantity, price, stop_price)
            else:
                # This path should now be unreachable if the initial check is correct
                order_type_str = order_type.value if hasattr(order_type, "value") else str(order_type)
                error_msg = f"Unsupported order type: {order_type_str}"
                logging.error(f"❌ {error_msg}")
                return None

            OrderErrorHandler.log_operation_success("ORDER PLACEMENT", order)
            return order
        except (APIError, ValueError) as e:
            OrderErrorHandler.log_operation_failure("ORDER PLACEMENT", e)
            return None

    def _validate_order_request(
        self, symbol: str, side: OrderSide, order_type: OrderType, quantity: float, price: float | None, stop_price: float | None
    ) -> None:
        """Validate order request and raise ValueError if invalid.

        This method consolidates all validation logic in one place.
        """
        # Get lot size info for user awareness
        lot_size_info = self._order_validator.get_lot_size_info_display(symbol)
        logging.info(f"📏 Lot Size Info (automatic check):\n{lot_size_info}")

        # Validate order placement constraints
        is_valid, validation_errors = self._order_validator.validate_order_placement(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        if not is_valid:
            error_msg = OrderErrorHandler.format_validation_error(symbol, validation_errors)
            logging.error(error_msg)
            logging.error(f"📏 LOT SIZE REQUIREMENTS:\n{lot_size_info}")
            raise ValueError(f"Order validation failed: {'; '.join(validation_errors)}")

        # Validate order type enum (simplified validation)
        # Note: order_type is already typed as OrderType, so isinstance check is redundant

        logging.info(f"✅ Order validation passed for {symbol} (lot size automatically verified)")

    def _validate_required_params(self, order_type: OrderType, price: float | None, stop_price: float | None) -> None:
        """Validate that required parameters are provided for specific order types."""
        if order_type == OrderType.LIMIT and price is None:
            error_msg = OrderErrorHandler.format_parameter_error(order_type, "price")
            raise ValueError(error_msg)
        elif order_type == OrderType.STOP_LOSS and stop_price is None:
            error_msg = OrderErrorHandler.format_parameter_error(order_type, "stop_price")
            raise ValueError(error_msg)
        elif order_type == OrderType.TAKE_PROFIT and stop_price is None:
            error_msg = OrderErrorHandler.format_parameter_error(order_type, "stop_price")
            raise ValueError(error_msg)
        elif order_type == OrderType.OCO and (price is None or stop_price is None):
            error_msg = OrderErrorHandler.format_parameter_error(order_type, "price and stop_price")
            raise ValueError(error_msg)

    def _place_market_order(self, symbol: str, side: OrderSide, quantity: float) -> Order:
        """Place a market order."""
        return self._client.place_market_order(symbol=symbol, side=side, quantity=quantity)

    def _place_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float) -> Order:
        """Place a limit order with precision formatting."""
        formatted_qty, formatted_price = self._precision_formatter.format_limit_params(symbol, quantity, price)
        logging.info(f"LIMIT order formatted: qty {quantity} → {formatted_qty}, price {price} → {formatted_price}")
        return self._client.place_limit_order(symbol=symbol, side=side, quantity=formatted_qty, price=formatted_price)

    def _place_stop_loss_order(self, symbol: str, side: OrderSide, quantity: float, stop_price: float) -> Order:
        """Place a stop loss order."""
        return self._client.place_stop_loss_order(symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)

    def _place_take_profit_order(self, symbol: str, side: OrderSide, quantity: float, stop_price: float) -> Order:
        """Place a take profit order."""
        return self._client.place_take_profit_order(symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)

    def _place_oco_order(self, symbol: str, quantity: float, price: float, stop_price: float) -> OcoOrder:
        """Place an OCO order with precision formatting and detailed error handling."""
        formatted_qty, formatted_price, formatted_stop = self._precision_formatter.format_oco_params(symbol, quantity, price, stop_price)
        logging.info(
            f"OCO order validated and formatted: qty {quantity} → {formatted_qty}, price {price} → {formatted_price}, stop {stop_price} → {formatted_stop}"
        )

        try:
            # OCO orders are always SELL side in this implementation
            result = self._client.place_oco_order(symbol=symbol, side=OrderSide.SELL, quantity=formatted_qty, price=formatted_price, stop_price=formatted_stop)
            return cast(OcoOrder, result)
        except APIError as api_error:
            error_details = {
                "Symbol": symbol,
                "Formatted Quantity": formatted_qty,
                "Formatted Price": formatted_price,
                "Formatted Stop Price": formatted_stop,
                "API Response": str(api_error),
            }
            error_msg = OrderErrorHandler.format_api_error("OCO ORDER PLACEMENT", symbol, error_details)
            logging.error(error_msg)
            raise api_error

    def cancel_order(
        self,
        order_type: OrderType,
        symbol: str,
        order_id: int | None = None,
        order_list_id: int | None = None,
    ) -> Order | OcoOrder | None:
        """Cancels an active order or OCO order.

        Args:
            order_type: The type of order to cancel (e.g., OCO).
            symbol: The trading symbol.
            order_id: The ID of the standard order to cancel.
            order_list_id: The ID of the OCO order list to cancel.

        Returns:
            An `Order` TypedDict with the details of the canceled order, or
            None if the cancellation fails.

        Raises:
            ValueError: If the required ID (order_id or order_list_id) is missing.
        """
        try:
            OrderErrorHandler.log_operation_start("ORDER CANCELLATION", symbol, OrderSide.SELL, order_type, 0)

            result: Order | OcoOrder | None
            if order_type == OrderType.OCO:
                if not order_list_id:
                    error_msg = OrderErrorHandler.format_parameter_error(order_type, "order_list_id")
                    raise ValueError(error_msg)
                result = self._client.cancel_oco_order(symbol=symbol, order_list_id=order_list_id)
            else:
                if not order_id:
                    error_msg = f"❌ PARAMETER ERROR: order_id is required to cancel a standard {order_type.value} order"
                    raise ValueError(error_msg)
                result = self._client.cancel_order(symbol=symbol, order_id=order_id)

            OrderErrorHandler.log_operation_success("ORDER CANCELLATION", result)
            return result
        except (APIError, ValueError) as e:
            OrderErrorHandler.log_operation_failure("ORDER CANCELLATION", e)
            raise e
