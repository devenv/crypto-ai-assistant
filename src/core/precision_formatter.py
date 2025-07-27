"""Precision formatting utility for Binance order parameters."""

import logging
from decimal import ROUND_DOWN, Decimal
from typing import Any

from api.client import BinanceClient

logger = logging.getLogger(__name__)


class PrecisionFormatter:
    """Formats order quantities and prices to match Binance exchange constraints."""

    def __init__(self, client: BinanceClient):
        """Initialize the PrecisionFormatter.

        Args:
            client: BinanceClient instance for API calls.
        """
        self._client = client
        self._symbol_cache: dict[str, dict[str, Any]] = {}

    def format_quantity(self, symbol: str, quantity: float) -> float:
        """Format quantity to match LOT_SIZE step size.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT').
            quantity: Raw quantity value.

        Returns:
            Formatted quantity aligned with step size.
        """
        step_size = self._get_lot_size_step(symbol)
        if not step_size:
            return quantity

        # Use Decimal for precision
        qty_decimal = Decimal(str(quantity))
        step_decimal = Decimal(str(step_size))

        # Calculate aligned quantity: floor((qty - minQty) / stepSize) * stepSize + minQty
        min_qty = self._get_lot_size_min(symbol)
        min_decimal = Decimal(str(min_qty))

        steps = ((qty_decimal - min_decimal) / step_decimal).quantize(Decimal("1"), rounding=ROUND_DOWN)
        aligned_qty = steps * step_decimal + min_decimal

        return float(aligned_qty)

    def format_price(self, symbol: str, price: float) -> float:
        """Format price to match PRICE_FILTER tick size.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT').
            price: Raw price value.

        Returns:
            Formatted price aligned with tick size.
        """
        tick_size = self._get_price_tick_size(symbol)
        if not tick_size:
            return price

        # Use Decimal for precision
        price_decimal = Decimal(str(price))
        tick_decimal = Decimal(str(tick_size))

        # Round to nearest tick: round(price / tickSize) * tickSize
        ticks = (price_decimal / tick_decimal).quantize(Decimal("1"))
        aligned_price = ticks * tick_decimal

        return float(aligned_price)

    def _get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Get cached symbol information."""
        if symbol not in self._symbol_cache:
            try:
                exchange_info = self._client.get_exchange_info(symbol)
                if exchange_info and "symbols" in exchange_info:
                    symbol_data = exchange_info["symbols"][0]
                    filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}
                    self._symbol_cache[symbol] = filters
                else:
                    self._symbol_cache[symbol] = {}
            except Exception as e:
                logger.error(f"Failed to get symbol info for {symbol}: {e}")
                self._symbol_cache[symbol] = {}

        return self._symbol_cache[symbol]

    def _get_lot_size_step(self, symbol: str) -> float | None:
        """Get LOT_SIZE step size for symbol."""
        filters = self._get_symbol_info(symbol)
        lot_filter = filters.get("LOT_SIZE")
        if lot_filter and "stepSize" in lot_filter:
            return float(lot_filter["stepSize"])
        return None

    def _get_lot_size_min(self, symbol: str) -> float:
        """Get LOT_SIZE minimum quantity for symbol."""
        filters = self._get_symbol_info(symbol)
        lot_filter = filters.get("LOT_SIZE")
        if lot_filter and "minQty" in lot_filter:
            return float(lot_filter["minQty"])
        return 0.0

    def _get_price_tick_size(self, symbol: str) -> float | None:
        """Get PRICE_FILTER tick size for symbol."""
        filters = self._get_symbol_info(symbol)
        price_filter = filters.get("PRICE_FILTER")
        if price_filter and "tickSize" in price_filter:
            return float(price_filter["tickSize"])
        return None

    def format_oco_params(self, symbol: str, quantity: float, limit_price: float, stop_price: float) -> tuple[float, float, float]:
        """Format all OCO order parameters for precision.

        Args:
            symbol: Trading symbol.
            quantity: Order quantity.
            limit_price: Take-profit price.
            stop_price: Stop-loss price.

        Returns:
            Tuple of (formatted_quantity, formatted_limit_price, formatted_stop_price).
        """
        formatted_qty = self.format_quantity(symbol, quantity)
        formatted_limit = self.format_price(symbol, limit_price)
        formatted_stop = self.format_price(symbol, stop_price)

        logger.info(f"OCO formatting for {symbol}:")
        logger.info(f"  Quantity: {quantity} → {formatted_qty}")
        logger.info(f"  Limit Price: {limit_price} → {formatted_limit}")
        logger.info(f"  Stop Price: {stop_price} → {formatted_stop}")

        return formatted_qty, formatted_limit, formatted_stop

    def format_limit_params(self, symbol: str, quantity: float, price: float) -> tuple[float, float]:
        """Format limit order parameters for precision.

        Args:
            symbol: Trading symbol.
            quantity: Order quantity.
            price: Order price.

        Returns:
            Tuple of (formatted_quantity, formatted_price).
        """
        formatted_qty = self.format_quantity(symbol, quantity)
        formatted_price = self.format_price(symbol, price)

        logger.info(f"Limit order formatting for {symbol}:")
        logger.info(f"  Quantity: {quantity} → {formatted_qty}")
        logger.info(f"  Price: {price} → {formatted_price}")

        return formatted_qty, formatted_price
