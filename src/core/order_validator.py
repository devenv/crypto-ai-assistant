"""Order validation utility for pre-checking Binance API constraints."""

import logging
from typing import Any, Dict, List, Optional, Tuple, cast

from api.client import BinanceClient
from api.enums import OrderSide

logger = logging.getLogger(__name__)


class OrderValidator:
    """Validates orders against exchange filters before placement."""

    def __init__(self, client: BinanceClient):
        """Initialize the OrderValidator.

        Args:
            client: BinanceClient instance for API calls.
        """
        self._client = client

    def validate_oco_order(
        self,
        symbol: str,
        quantity: float,
        limit_price: float,
        stop_price: float,
    ) -> Tuple[bool, List[str]]:
        """Validate OCO order parameters against exchange constraints.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT').
            quantity: Order quantity.
            limit_price: Take-profit price.
            stop_price: Stop-loss price.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []

        try:
            # Get symbol info and current price
            symbol_info_raw = self._client.get_exchange_info(symbol)
            current_price = self._get_current_price(symbol)

            if not symbol_info_raw or not current_price:
                errors.append("Could not retrieve symbol information or current price")
                return False, errors

            # Work with the API response as raw dict to avoid TypedDict issues
            symbol_info = cast(Dict[str, Any], symbol_info_raw)
            symbols_list = symbol_info.get("symbols", [])
            if not symbols_list:
                errors.append("No symbol information found")
                return False, errors

            symbol_data = symbols_list[0]
            # Extract filters as dict - no need to cast filterType since it's already str
            filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}

            # Validate LOT_SIZE
            lot_errors = self._validate_lot_size(quantity, filters.get("LOT_SIZE"))
            errors.extend(lot_errors)

            # Validate PRICE_FILTER
            price_errors = self._validate_price_filter([limit_price, stop_price], filters.get("PRICE_FILTER"))
            errors.extend(price_errors)

            # Validate OCO price logic (SELL side)
            if limit_price <= current_price:
                errors.append(f"OCO limit price ${limit_price:,.2f} must be ABOVE current price ${current_price:,.2f}")

            if stop_price >= current_price:
                errors.append(f"OCO stop price ${stop_price:,.2f} must be BELOW current price ${current_price:,.2f}")

            if limit_price <= stop_price:
                errors.append(f"OCO limit price ${limit_price:,.2f} must be ABOVE stop price ${stop_price:,.2f}")

            # Validate PERCENT_PRICE_BY_SIDE
            percent_errors = self._validate_percent_price([limit_price, stop_price], current_price, filters.get("PERCENT_PRICE_BY_SIDE"), OrderSide.SELL)
            errors.extend(percent_errors)

            # Validate NOTIONAL
            notional_errors = self._validate_notional(quantity, [limit_price, stop_price], filters.get("NOTIONAL"))
            errors.extend(notional_errors)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def validate_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
    ) -> Tuple[bool, List[str]]:
        """Validate limit order parameters against exchange constraints.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT').
            side: Order side (BUY or SELL).
            quantity: Order quantity.
            price: Order price.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []

        try:
            # Get symbol info and current price
            symbol_info_raw = self._client.get_exchange_info(symbol)
            current_price = self._get_current_price(symbol)

            if not symbol_info_raw or not current_price:
                errors.append("Could not retrieve symbol information or current price")
                return False, errors

            # Work with the API response as raw dict to avoid TypedDict issues
            symbol_info = cast(Dict[str, Any], symbol_info_raw)
            symbols_list = symbol_info.get("symbols", [])
            if not symbols_list:
                errors.append("No symbol information found")
                return False, errors

            symbol_data = symbols_list[0]
            # Extract filters as dict - no need to cast filterType since it's already str
            filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}

            # Validate LOT_SIZE
            lot_errors = self._validate_lot_size(quantity, filters.get("LOT_SIZE"))
            errors.extend(lot_errors)

            # Validate PRICE_FILTER
            price_errors = self._validate_price_filter([price], filters.get("PRICE_FILTER"))
            errors.extend(price_errors)

            # Validate PERCENT_PRICE_BY_SIDE
            percent_errors = self._validate_percent_price([price], current_price, filters.get("PERCENT_PRICE_BY_SIDE"), side)
            errors.extend(percent_errors)

            # Validate NOTIONAL
            notional_errors = self._validate_notional(quantity, [price], filters.get("NOTIONAL"))
            errors.extend(notional_errors)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            tickers = self._client.get_all_tickers()
            for ticker in tickers:
                if ticker["symbol"] == symbol:
                    return float(ticker["price"])
            return None
        except Exception:
            return None

    def _validate_lot_size(self, quantity: float, lot_filter: Optional[Dict[str, Any]]) -> List[str]:
        """Validate quantity against LOT_SIZE filter."""
        errors: List[str] = []
        if not lot_filter:
            return errors

        min_qty = float(lot_filter.get("minQty", 0))
        max_qty = float(lot_filter.get("maxQty", float("inf")))
        step_size = float(lot_filter.get("stepSize", 0))

        if quantity < min_qty:
            errors.append(f"Quantity {quantity} below minimum {min_qty}")
        if quantity > max_qty:
            errors.append(f"Quantity {quantity} above maximum {max_qty}")
        if step_size > 0:
            # Use proper floating point comparison for step size alignment
            diff = quantity - min_qty
            remainder = abs(diff % step_size)
            if remainder > 1e-8 and abs(remainder - step_size) > 1e-8:
                errors.append(f"Quantity {quantity} not aligned with step size {step_size}")

        return errors

    def _validate_price_filter(self, prices: List[float], price_filter: Optional[Dict[str, Any]]) -> List[str]:
        """Validate prices against PRICE_FILTER."""
        errors: List[str] = []
        if not price_filter:
            return errors

        min_price = float(price_filter.get("minPrice", 0))
        max_price = float(price_filter.get("maxPrice", float("inf")))
        tick_size = float(price_filter.get("tickSize", 0))

        for price in prices:
            if min_price > 0 and price < min_price:
                errors.append(f"Price ${price:,.8f} below minimum ${min_price:,.8f}")
            if max_price > 0 and price > max_price:
                errors.append(f"Price ${price:,.8f} above maximum ${max_price:,.8f}")
            if tick_size > 0:
                # Use proper floating point comparison for tick size alignment
                remainder = abs(price % tick_size)
                if remainder > 1e-8 and abs(remainder - tick_size) > 1e-8:
                    errors.append(f"Price ${price:,.8f} not aligned with tick size ${tick_size:,.8f}")

        return errors

    def _validate_percent_price(self, prices: List[float], current_price: float, percent_filter: Optional[Dict[str, Any]], side: OrderSide) -> List[str]:
        """Validate prices against PERCENT_PRICE_BY_SIDE filter."""
        errors: List[str] = []
        if not percent_filter:
            return errors

        if side == OrderSide.BUY:
            multiplier_up = float(percent_filter.get("bidMultiplierUp", 5))
            multiplier_down = float(percent_filter.get("bidMultiplierDown", 0.2))
        else:  # SELL
            multiplier_up = float(percent_filter.get("askMultiplierUp", 5))
            multiplier_down = float(percent_filter.get("askMultiplierDown", 0.2))

        max_price = current_price * multiplier_up
        min_price = current_price * multiplier_down

        for price in prices:
            if price > max_price:
                errors.append(f"Price ${price:,.2f} above {side.value} limit ${max_price:,.2f} ({multiplier_up}x current)")
            if price < min_price:
                errors.append(f"Price ${price:,.2f} below {side.value} limit ${min_price:,.2f} ({multiplier_down}x current)")

        return errors

    def _validate_notional(self, quantity: float, prices: List[float], notional_filter: Optional[Dict[str, Any]]) -> List[str]:
        """Validate notional value against NOTIONAL filter."""
        errors: List[str] = []
        if not notional_filter:
            return errors

        min_notional = float(notional_filter.get("minNotional", 0))
        max_notional = float(notional_filter.get("maxNotional", float("inf")))

        for price in prices:
            notional = quantity * price
            if notional < min_notional:
                errors.append(f"Notional ${notional:,.2f} below minimum ${min_notional:,.2f}")
            if notional > max_notional:
                errors.append(f"Notional ${notional:,.2f} above maximum ${max_notional:,.2f}")

        return errors
