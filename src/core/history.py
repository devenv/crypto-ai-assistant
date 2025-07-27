"""Trading History Management Module.

This module provides functionality for retrieving and managing
trading history data from the Binance API.
"""

from __future__ import annotations

from typing import cast

from api.client import BinanceClient
from api.models import Trade


class HistoryService:
    """Provides methods for fetching historical trade data."""

    def __init__(self, client: BinanceClient):
        """Initializes the HistoryService.

        Args:
            client: An instance of `BinanceClient` to interact with the API.
        """
        self._client = client

    def get_trade_history(self, symbol: str, limit: int = 10) -> list[Trade]:
        """Fetches trade history for a given symbol.

        Args:
            symbol: The symbol to get history for (e.g., "BTCUSDT").
            limit: The number of trades to retrieve.

        Returns:
            A list of `Trade` TypedDicts, where each object represents a trade.
        """
        result = self._client.get_trade_history(symbol=symbol, limit=limit)
        return cast(list[Trade], result)
