from typing import List

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

    def get_trade_history(self, symbol: str, limit: int = 10) -> List[Trade]:
        """Fetches trade history for a given symbol.

        Args:
            symbol: The symbol to get history for (e.g., "BTCUSDT").
            limit: The number of trades to retrieve.

        Returns:
            A list of `Trade` TypedDicts, where each object represents a trade.
        """
        return self._client.get_trade_history(symbol=symbol, limit=limit)
