from typing import cast

from api.client import BinanceClient
from api.models import SymbolInfo


class ExchangeService:
    """Provides methods for fetching exchange information."""

    def __init__(self, client: BinanceClient):
        """Initializes the ExchangeService.

        Args:
            client: An instance of `BinanceClient` to interact with the API.
        """
        self._client = client

    def get_lot_size_info(self, symbol: str) -> str | None:
        """Fetches and returns the LOT_SIZE stepSize for a given symbol.

        The step size determines the number of decimal places allowed for the
        quantity of an order.

        Args:
            symbol: The trading symbol (e.g., "BTCUSDT").

        Returns:
            The step size as a string (e.g., "0.00100000"), or None if the
            information could not be retrieved.
        """
        try:
            info = self._client.get_exchange_info(symbol=symbol)
            if not info:
                return None

            # The structure is data['symbols'][0]['filters']
            symbol_info = info.get("symbols", [])
            if not symbol_info:
                return None

            for f in symbol_info[0].get("filters", []):
                if f.get("filterType") == "LOT_SIZE":
                    return cast(str, f.get("stepSize"))

            return None
        except Exception:
            return None

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Fetches and returns all filters for a given symbol.

        Args:
            symbol: The trading symbol (e.g., "BTCUSDT").

        Returns:
            A dictionary containing all symbol information, or None if the
            information could not be retrieved.
        """
        try:
            info = self._client.get_exchange_info(symbol=symbol)
            if not info:
                return None

            symbol_info = info.get("symbols", [])
            if not symbol_info:
                return None

            return symbol_info[0]
        except Exception:
            return None
