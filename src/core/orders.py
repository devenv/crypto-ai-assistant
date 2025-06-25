import logging
from typing import List, Optional, Union

from api.client import BinanceClient
from api.enums import OrderSide, OrderType
from api.exceptions import APIError
from api.models import OcoOrder, Order


class OrderService:
    """Provides methods for placing and managing orders."""

    def __init__(self, client: BinanceClient) -> None:
        """Initializes the OrderService.

        Args:
            client: An instance of `BinanceClient` to interact with the API.
        """
        self._client = client

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Fetches open orders for a specific symbol or all symbols.

        Args:
            symbol: The trading symbol to fetch open orders for. If None,
                fetches open orders for all symbols.

        Returns:
            A list of `Order` TypedDicts representing the open orders.
        """
        return self._client.get_open_orders(symbol=symbol)

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Optional[Union[Order, OcoOrder]]:
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
            if not isinstance(order_type, OrderType) or order_type.value not in [o.value for o in OrderType]:
                logging.error(f"Unsupported order type: {order_type}")
                return None

            logging.info(f"Attempting to place {side.value} {order_type.value} order for {quantity} of {symbol}")
            order: Optional[Union[Order, OcoOrder]] = None
            if order_type == OrderType.MARKET:
                order = self._client.place_market_order(symbol=symbol, side=side, quantity=quantity)
            elif order_type == OrderType.LIMIT:
                if price is None:
                    raise ValueError("Price is required for LIMIT orders.")
                order = self._client.place_limit_order(symbol=symbol, side=side, quantity=quantity, price=price)
            elif order_type == OrderType.STOP_LOSS:
                if stop_price is None:
                    raise ValueError("Stop price is required for STOP_LOSS orders.")
                order = self._client.place_stop_loss_order(symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)
            elif order_type == OrderType.TAKE_PROFIT:
                if stop_price is None:
                    raise ValueError("Stop price is required for TAKE_PROFIT orders.")
                order = self._client.place_take_profit_order(symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)
            elif order_type == OrderType.OCO:
                if price is None or stop_price is None:
                    raise ValueError("Price and stop_price are required for OCO orders.")
                # OCO orders are always SELL side in this implementation
                order = self._client.place_oco_order(symbol=symbol, side=OrderSide.SELL, quantity=quantity, price=price, stop_price=stop_price)
            else:
                # This path should now be unreachable if the initial check is correct
                logging.error(f"Unsupported order type: {order_type.value}")
                return None

            logging.info(f"Order placed successfully: {order}")
            return order
        except (APIError, ValueError) as e:
            logging.error(f"Failed to place order: {e}")
            return None

    def cancel_order(
        self,
        order_type: OrderType,
        symbol: str,
        order_id: Optional[int] = None,
        order_list_id: Optional[int] = None,
    ) -> Optional[Union[Order, OcoOrder]]:
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
        logging.info(f"Canceling {order_type.value} order on {symbol}...")
        result: Optional[Union[Order, OcoOrder]]
        if order_type == OrderType.OCO:
            if not order_list_id:
                raise ValueError("order_list_id is required to cancel OCO orders.")  # pragma: no cover
            result = self._client.cancel_oco_order(symbol=symbol, order_list_id=order_list_id)
        else:
            if not order_id:
                raise ValueError("order_id is required to cancel a standard order.")  # pragma: no cover
            result = self._client.cancel_order(symbol=symbol, order_id=order_id)

        logging.info(f"Order canceled successfully: {result}")
        return result
