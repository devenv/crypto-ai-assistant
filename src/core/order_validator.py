"""Order validation utility for pre-checking Binance API constraints."""

import logging
from typing import Any, cast

from api.client import BinanceClient
from api.enums import OrderSide, OrderType

logger = logging.getLogger(__name__)


class OrderValidator:
    """Validates orders against exchange filters before placement."""

    def __init__(self, client: BinanceClient):
        """Initialize the OrderValidator.

        Args:
            client: BinanceClient instance for API calls.
        """
        self._client = client

    def validate_order_placement(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate order placement to prevent immediate fills and other issues.

        This is the main validation method that should be called before placing any order.
        It combines market price checks, precision validation, and exchange constraints.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT').
            side: Order side (BUY or SELL).
            order_type: Type of order (LIMIT, MARKET, OCO, etc.).
            quantity: Order quantity.
            price: Order price (for LIMIT/OCO orders).
            stop_price: Stop price (for OCO orders).

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors: list[str] = []

        try:
            # Get current market price
            current_price = self._get_current_price(symbol)
            if not current_price:
                errors.append(f"Could not retrieve current price for {symbol}")
                return False, errors

            # 1. Market Price Validation (prevent immediate fills)
            immediate_fill_errors = self._validate_immediate_fill_risk(side, order_type, price, stop_price, current_price)
            errors.extend(immediate_fill_errors)

            # 2. Route to specific validation based on order type
            if order_type == OrderType.OCO:
                if price is None or stop_price is None:
                    errors.append("Price and stop_price are required for OCO orders")
                    return False, errors
                oco_valid, oco_errors = self.validate_oco_order(symbol, quantity, price, stop_price)
                if not oco_valid:
                    errors.extend(oco_errors)
            elif order_type == OrderType.LIMIT:
                if price is None:
                    errors.append("Price is required for LIMIT orders")
                    return False, errors
                limit_valid, limit_errors = self.validate_limit_order(symbol, side, quantity, price)
                if not limit_valid:
                    errors.extend(limit_errors)
            # MARKET orders don't need price validation but should check quantities
            elif order_type == OrderType.MARKET:
                market_valid, market_errors = self._validate_market_order_constraints(symbol, quantity)
                if not market_valid:
                    errors.extend(market_errors)

            # 3. Always validate available balance for all order types
            balance_valid, balance_errors = self._validate_available_balance(symbol, side, quantity, price, current_price)
            if not balance_valid:
                errors.extend(balance_errors)

        except Exception as e:
            errors.append(f"Order validation error: {str(e)}")

        return len(errors) == 0, errors

    def get_lot_size_info_display(self, symbol: str) -> str:
        """Get user-friendly lot size information for a symbol.

        This replaces the need for manual 'exchange lotsize' commands.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT').

        Returns:
            Formatted string with lot size information.
        """
        try:
            symbol_info_raw = self._client.get_exchange_info(symbol)
            if not symbol_info_raw:
                return f"❌ Could not retrieve lot size info for {symbol}"

            symbol_info = cast(dict[str, Any], symbol_info_raw)
            symbols_list = symbol_info.get("symbols", [])
            if not symbols_list:
                return f"❌ No symbol information found for {symbol}"

            symbol_data = symbols_list[0]
            filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}
            lot_filter = filters.get("LOT_SIZE")

            if not lot_filter:
                return f"❌ No LOT_SIZE filter found for {symbol}"

            step_size = float(lot_filter.get("stepSize", 0))
            min_qty = float(lot_filter.get("minQty", 0))
            max_qty = float(lot_filter.get("maxQty", float("inf")))

            # Calculate decimal places
            step_str = str(step_size)
            if "." in step_str:
                decimal_places = len(step_str.split(".")[1].rstrip("0"))
            else:
                decimal_places = 0

            return (
                f"📏 {symbol} LOT_SIZE Requirements:\n"
                f"   • Step Size: {step_size} ({decimal_places} decimal places)\n"
                f"   • Minimum: {min_qty}\n"
                f"   • Maximum: {max_qty}\n"
                f"   • Example Valid Quantities: {min_qty}, {min_qty + step_size:.{decimal_places}f}, {min_qty + 2 * step_size:.{decimal_places}f}"
            )

        except Exception as e:
            return f"❌ Error retrieving lot size info for {symbol}: {str(e)}"

    def _validate_immediate_fill_risk(
        self,
        side: OrderSide,
        order_type: OrderType,
        price: float | None,
        stop_price: float | None,
        current_price: float,
    ) -> list[str]:
        """Check if order would fill immediately due to wrong price side.

        This prevents the critical error where orders execute immediately instead of waiting.
        """
        errors: list[str] = []

        if order_type == OrderType.MARKET:
            # Market orders are supposed to fill immediately
            return errors

        if order_type == OrderType.LIMIT and price is not None:
            if side == OrderSide.SELL and price <= current_price:
                errors.append(
                    f"🚨 CRITICAL: SELL LIMIT at ${price:,.2f} would fill IMMEDIATELY "
                    + f"(current price: ${current_price:,.2f}). For profit-taking, use price > ${current_price:,.2f}"
                )
            elif side == OrderSide.BUY and price >= current_price:
                errors.append(
                    f"🚨 CRITICAL: BUY LIMIT at ${price:,.2f} would fill IMMEDIATELY "
                    + f"(current price: ${current_price:,.2f}). For accumulation, use price < ${current_price:,.2f}"
                )

        if order_type == OrderType.OCO:
            # For OCO orders (SELL side protection), both limits must be on correct sides
            if price is not None and price <= current_price:
                errors.append(
                    f"🚨 CRITICAL: OCO limit price ${price:,.2f} would fill IMMEDIATELY "
                    + f"(current price: ${current_price:,.2f}). Take-profit must be > ${current_price:,.2f}"
                )
            if stop_price is not None and stop_price >= current_price:
                errors.append(
                    f"🚨 CRITICAL: OCO stop price ${stop_price:,.2f} would trigger IMMEDIATELY "
                    + f"(current price: ${current_price:,.2f}). Stop-loss must be < ${current_price:,.2f}"
                )

        return errors

    def _validate_available_balance(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float | None,
        current_price: float,
    ) -> tuple[bool, list[str]]:
        """Validate that sufficient balance is available for the order, accounting for existing orders."""
        errors: list[str] = []

        try:
            # Import here to avoid circular dependency
            from core.account import AccountService

            account_service = AccountService(self._client)

            if side == OrderSide.BUY:
                # For BUY orders, need enough USDT (or quote currency)
                quote_asset = "USDT"  # Assuming USDT pairs for now
                effective_price = price if price else current_price
                required_amount = quantity * effective_price

                # Get effective available balance (accounts for existing orders)
                available_balance, commitments = account_service.get_effective_available_balance(quote_asset)

                if available_balance < required_amount:
                    errors.append(
                        f"Insufficient effective {quote_asset} balance: have ${available_balance:,.2f} available "
                        + f"(${commitments.get('buy_orders', 0):,.2f} committed to buy orders), "
                        + f"need ${required_amount:,.2f} for {quantity} {symbol} at ${effective_price:,.2f}"
                    )

            else:  # OrderSide.SELL
                # For SELL orders, need enough of the base asset
                base_asset = symbol.replace("USDT", "").replace("BUSD", "").replace("BTC", "")  # Simple extraction

                # Get effective available balance (accounts for existing orders)
                available_balance, commitments = account_service.get_effective_available_balance(base_asset)

                if available_balance < quantity:
                    errors.append(
                        f"Insufficient effective {base_asset} balance: have {available_balance:,.8f} available "
                        + f"({commitments.get('sell_orders', 0):,.8f} committed to sell orders, "
                        + f"{commitments.get('oco_orders', 0):,.8f} in OCO orders), "
                        + f"need {quantity:,.8f} to sell"
                    )

        except Exception as e:
            errors.append(f"Balance validation error: {str(e)}")

        return len(errors) == 0, errors

    def _get_symbol_validation_data(self, symbol: str) -> tuple[dict[str, Any] | None, float | None, list[str]]:
        """Get symbol information and current price for validation.

        Returns:
            Tuple of (filters_dict, current_price, errors).
        """
        errors: list[str] = []

        try:
            # Get symbol info and current price
            symbol_info_raw = self._client.get_exchange_info(symbol)
            current_price = self._get_current_price(symbol)

            if not symbol_info_raw or not current_price:
                errors.append("Could not retrieve symbol information or current price")
                return None, None, errors

            # Work with the API response as raw dict to avoid TypedDict issues
            symbol_info = cast(dict[str, Any], symbol_info_raw)
            symbols_list = symbol_info.get("symbols", [])
            if not symbols_list:
                errors.append("No symbol information found")
                return None, None, errors

            symbol_data = symbols_list[0]
            # Extract filters as dict - no need to cast filterType since it's already str
            filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}

            return filters, current_price, errors

        except Exception as e:
            errors.append(f"Symbol validation data error: {str(e)}")
            return None, None, errors

    def _validate_exchange_constraints(self, quantity: float, prices: list[float], filters: dict[str, Any], current_price: float, side: OrderSide) -> list[str]:
        """Validate common exchange constraints for all order types.

        Args:
            quantity: Order quantity.
            prices: List of prices to validate.
            filters: Exchange filters dict.
            current_price: Current market price.
            side: Order side.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        # Validate LOT_SIZE
        lot_errors = self._validate_lot_size(quantity, filters.get("LOT_SIZE"))
        errors.extend(lot_errors)

        # Validate PRICE_FILTER
        price_errors = self._validate_price_filter(prices, filters.get("PRICE_FILTER"))
        errors.extend(price_errors)

        # Validate PERCENT_PRICE_BY_SIDE
        percent_errors = self._validate_percent_price(prices, current_price, filters.get("PERCENT_PRICE_BY_SIDE"), side)
        errors.extend(percent_errors)

        # Validate NOTIONAL
        notional_errors = self._validate_notional(quantity, prices, filters.get("NOTIONAL"))
        errors.extend(notional_errors)

        return errors

    def _validate_market_order_constraints(self, symbol: str, quantity: float) -> tuple[bool, list[str]]:
        """Validate market order against basic exchange constraints."""
        errors: list[str] = []

        try:
            # Use consolidated method to get validation data
            filters, current_price, setup_errors = self._get_symbol_validation_data(symbol)
            errors.extend(setup_errors)

            if not filters or not current_price:
                return False, errors

            # For market orders, only validate LOT_SIZE (no price constraints)
            lot_errors = self._validate_lot_size(quantity, filters.get("LOT_SIZE"))
            errors.extend(lot_errors)

        except Exception as e:
            errors.append(f"Market order validation error: {str(e)}")

        return len(errors) == 0, errors

    def validate_oco_order(
        self,
        symbol: str,
        quantity: float,
        limit_price: float,
        stop_price: float,
    ) -> tuple[bool, list[str]]:
        """Validate OCO order parameters against exchange constraints.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT').
            quantity: Order quantity.
            limit_price: Take-profit price.
            stop_price: Stop-loss price.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors: list[str] = []

        try:
            # Use consolidated method to get validation data
            filters, current_price, setup_errors = self._get_symbol_validation_data(symbol)
            errors.extend(setup_errors)

            if not filters or not current_price:
                return False, errors

            # Validate OCO-specific price logic (SELL side)
            if limit_price <= current_price:
                errors.append(f"OCO limit price ${limit_price:,.2f} must be ABOVE current price ${current_price:,.2f}")

            if stop_price >= current_price:
                errors.append(f"OCO stop price ${stop_price:,.2f} must be BELOW current price ${current_price:,.2f}")

            if limit_price <= stop_price:
                errors.append(f"OCO limit price ${limit_price:,.2f} must be ABOVE stop price ${stop_price:,.2f}")

            # Use consolidated method for exchange constraints
            constraint_errors = self._validate_exchange_constraints(
                quantity=quantity,
                prices=[limit_price, stop_price],
                filters=filters,
                current_price=current_price,
                side=OrderSide.SELL,  # OCO orders are SELL side in this implementation
            )
            errors.extend(constraint_errors)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def validate_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
    ) -> tuple[bool, list[str]]:
        """Validate limit order parameters against exchange constraints.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT').
            side: Order side (BUY or SELL).
            quantity: Order quantity.
            price: Order price.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors: list[str] = []

        try:
            # Use consolidated method to get validation data
            filters, current_price, setup_errors = self._get_symbol_validation_data(symbol)
            errors.extend(setup_errors)

            if not filters or not current_price:
                return False, errors

            # Use consolidated method for exchange constraints
            constraint_errors = self._validate_exchange_constraints(quantity=quantity, prices=[price], filters=filters, current_price=current_price, side=side)
            errors.extend(constraint_errors)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def _get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        try:
            tickers = self._client.get_all_tickers()
            for ticker in tickers:
                if ticker["symbol"] == symbol:
                    return float(ticker["price"])
            return None
        except Exception:
            return None

    def _validate_lot_size(self, quantity: float, lot_filter: dict[str, Any] | None) -> list[str]:
        """Validate quantity against LOT_SIZE filter with user-friendly error messages."""
        errors: list[str] = []
        if not lot_filter:
            return errors

        min_qty = float(lot_filter.get("minQty", 0))
        max_qty = float(lot_filter.get("maxQty", float("inf")))
        step_size = float(lot_filter.get("stepSize", 0))

        # Calculate decimal places for user-friendly formatting
        step_str = str(step_size)
        if "." in step_str:
            decimal_places = len(step_str.split(".")[1].rstrip("0"))
        else:
            decimal_places = 0

        if quantity < min_qty:
            errors.append(f"❌ QUANTITY TOO SMALL: {quantity} below minimum {min_qty} (exchange requirement)")
        if quantity > max_qty:
            errors.append(f"❌ QUANTITY TOO LARGE: {quantity} above maximum {max_qty} (exchange requirement)")
        if step_size > 0:
            # Use proper floating point comparison for step size alignment
            diff = quantity - min_qty
            remainder = abs(diff % step_size)
            if remainder > 1e-8 and abs(remainder - step_size) > 1e-8:
                # Calculate the correctly aligned quantity
                steps = int((quantity - min_qty) / step_size)
                suggested_qty = steps * step_size + min_qty
                errors.append(
                    f"❌ PRECISION ERROR: Quantity {quantity} not aligned with step size {step_size} "
                    + f"({decimal_places} decimal places). SUGGESTED: {suggested_qty:.{decimal_places}f}"
                )

        return errors

    def _validate_price_filter(self, prices: list[float], price_filter: dict[str, Any] | None) -> list[str]:
        """Validate prices against PRICE_FILTER."""
        errors: list[str] = []
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

    def _validate_percent_price(self, prices: list[float], current_price: float, percent_filter: dict[str, Any] | None, side: OrderSide) -> list[str]:
        """Validate prices against PERCENT_PRICE_BY_SIDE filter."""
        errors: list[str] = []
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

    def _validate_notional(self, quantity: float, prices: list[float], notional_filter: dict[str, Any] | None) -> list[str]:
        """Validate notional value against NOTIONAL filter."""
        errors: list[str] = []
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
