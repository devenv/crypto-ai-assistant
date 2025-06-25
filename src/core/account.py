from typing import Any, Dict, List, Optional

from api.client import BinanceClient
from api.exceptions import APIError


class AccountService:
    """Provides methods for fetching and processing account information."""

    def __init__(self, client: BinanceClient):
        """Initializes the AccountService.

        Args:
            client: An instance of `BinanceClient` to interact with the API.
        """
        self._client = client

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Fetches and processes account balance and value information.

        This method retrieves the account's balances and calculates their
        value in USDT.

        Returns:
            A dictionary containing the list of balances and the total
            portfolio value in USDT, or None if the information could not be
            retrieved. The dictionary structure is as follows:
            {
                "balances": [
                    {
                        "asset": str,
                        "total": float,
                        "value_usdt": float
                    },
                    ...
                ],
                "total_portfolio_value": float
            }
        """
        try:
            account_info = self._client.get_account_info()
            all_tickers = self._client.get_all_tickers()

            if not account_info or not all_tickers:
                return None

            price_lookup = {ticker["symbol"]: float(ticker["price"]) for ticker in all_tickers if ticker["symbol"].endswith("USDT")}

            balances: List[Dict[str, Any]] = []
            total_portfolio_value = 0.0

            for balance in account_info.get("balances", []):
                asset = balance["asset"]
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0:
                    value_usdt = 0.0
                    if asset == "USDT":
                        value_usdt = total
                    elif f"{asset}USDT" in price_lookup:
                        price = price_lookup[f"{asset}USDT"]
                        value_usdt = total * price

                    total_portfolio_value += value_usdt
                    balances.append(
                        {
                            "asset": asset,
                            "total": total,
                            "value_usdt": value_usdt,
                        }
                    )

            return {
                "balances": balances,
                "total_portfolio_value": total_portfolio_value,
            }
        except APIError:
            raise
        except Exception:
            return None
