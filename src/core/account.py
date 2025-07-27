"""Account management service for Binance API operations."""

import logging
from typing import Any, cast

from api.client import BinanceClient
from api.exceptions import APIError, BinanceException
from api.models import Balance, ProcessedBalance

logger = logging.getLogger(__name__)


class AccountService:
    """Provides account-related functionality for the Binance API client."""

    def __init__(self, client: BinanceClient):
        """Initialize the AccountService.

        Args:
            client: The BinanceClient instance to use for API calls.
        """
        self.client = client

    def get_account_info(self) -> dict[str, Any] | None:
        """Fetch account information from Binance with enhanced error handling.

        Returns:
            Account information dictionary or None if an error occurs.
        """
        try:
            logger.debug("Fetching account information from Binance")
            account_info = self.client.get_account_info()
            logger.info("Successfully retrieved account information")
            return cast(dict[str, Any], account_info)
        except BinanceException as e:
            logger.error(f"Binance API error while fetching account info: {e}")
            return None
        except APIError as e:
            logger.error(f"API error while fetching account info: {e}")
            return None
        except ConnectionError as e:
            logger.error(f"Connection error while fetching account info: {e}")
            return None
        except TimeoutError as e:
            logger.error(f"Timeout error while fetching account info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching account info: {e}")
            return None

    def format_account_display(self, account_info: dict[str, Any], tickers: list[Any], min_value_filter: float = 10.0) -> dict[str, Any]:
        """Format account information for display with enhanced error handling.

        Args:
            account_info: Raw account information from Binance
            tickers: List of ticker price information
            min_value_filter: Minimum USD value to include in display

        Returns:
            Formatted account information dictionary
        """
        try:
            if not account_info:
                logger.warning("Invalid or empty account_info provided")
                return {"balances": [], "total_portfolio_value": 0.0, "error": "Invalid account data"}

            if not tickers:
                logger.warning("Invalid or empty tickers provided")
                tickers = []

            # Create price lookup for efficiency
            price_map: dict[str, float] = {}
            try:
                for ticker in tickers:
                    if isinstance(ticker, dict) and "symbol" in ticker and "price" in ticker:
                        # Type-safe extraction with explicit casting to break unknown type chain
                        symbol_value = cast(Any, ticker["symbol"])
                        price_value = cast(Any, ticker["price"])
                        if symbol_value is not None and price_value is not None:
                            symbol = str(symbol_value)
                            price = float(price_value)
                            price_map[symbol] = price
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing ticker data: {e}")

            formatted_balances: list[dict[str, Any]] = []
            total_value: float = 0.0

            # Process balances safely - cast to ensure proper typing
            raw_balances_data = account_info.get("balances", [])
            if not raw_balances_data:
                logger.warning("Balances data is empty")
                raw_balances_data = []

            for balance_data in raw_balances_data:
                try:
                    if not isinstance(balance_data, dict):
                        continue
                    # Cast to Balance type for proper type checking
                    balance: Balance = cast(Balance, balance_data)

                    asset: str = balance.get("asset", "UNKNOWN")
                    free_balance: float = float(balance.get("free", "0"))
                    locked_balance: float = float(balance.get("locked", "0"))
                    total_balance: float = free_balance + locked_balance

                    if total_balance <= 0:
                        continue

                    # Calculate USD value
                    usd_value: float = 0.0
                    if asset == "USDT":
                        usd_value = total_balance
                    else:
                        # Try different symbol combinations
                        possible_symbols: list[str] = [f"{asset}USDT", f"{asset}BUSD", f"{asset}USD"]
                        for symbol in possible_symbols:
                            if symbol in price_map:
                                usd_value = float(total_balance * price_map[symbol])
                                break

                    # Apply minimum value filter
                    if usd_value >= min_value_filter:
                        formatted_balances.append(
                            {
                                "asset": asset,
                                "total": total_balance,
                                "value_usdt": usd_value,
                            }
                        )
                        total_value += float(usd_value)

                except (ValueError, TypeError, KeyError) as e:
                    # Use balance_data for error logging since balance might not be defined if casting failed
                    if isinstance(balance_data, dict) and "asset" in balance_data:
                        asset_value = cast(Any, balance_data["asset"])
                        asset_name = str(asset_value) if asset_value is not None else "UNKNOWN"
                    else:
                        asset_name = "UNKNOWN"
                    logger.warning(f"Error processing balance for asset {asset_name}: {e}")
                    continue

            # Sort by value descending
            formatted_balances.sort(key=lambda x: cast(float, x["value_usdt"]), reverse=True)

            logger.info(f"Successfully formatted {len(formatted_balances)} balances, total value: ${total_value:,.2f}")

            return {
                "balances": formatted_balances,
                "total_portfolio_value": total_value,
            }

        except Exception as e:
            logger.error(f"Unexpected error in format_account_display: {e}")
            return {"balances": [], "total_portfolio_value": 0.0, "error": str(e)}

    def get_balances(self, min_value: float = 1.0) -> list[ProcessedBalance] | None:
        """Get account balances with USD values above minimum threshold.

        Args:
            min_value: Minimum USD value to include in results

        Returns:
            List of balance dictionaries or None if error occurs
        """
        try:
            logger.debug(f"Fetching balances with min_value={min_value}")

            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                logger.error("Failed to get account info for balances")
                return None

            # Get ticker prices
            try:
                tickers = self.client.get_all_tickers()
                if not tickers:
                    logger.warning("Failed to get ticker prices, continuing with zero prices")
                    tickers = []
            except Exception as e:
                logger.warning(f"Error getting tickers: {e}, continuing with zero prices")
                tickers = []

            # Format the account display
            formatted_data = self.format_account_display(account_info, tickers, min_value)

            if "error" in formatted_data:
                logger.error(f"Error in format_account_display: {formatted_data['error']}")
                return None

            balances_data = formatted_data.get("balances", [])
            if not isinstance(balances_data, list):
                logger.error(f"Invalid balances data type: expected list, got {type(balances_data)}")
                return []
            # Return the balances data without redundant cast
            return balances_data

        except Exception as e:
            logger.error(f"Unexpected error in get_balances: {e}")
            return None

    def get_effective_available_balance(self, asset: str) -> tuple[float, dict[str, float]]:
        """Get available balance for an asset accounting for existing orders.

        Args:
            asset: Asset symbol (e.g., "BTC", "USDT", "SOL")

        Returns:
            Tuple of (available_balance, commitments_dict)
            commitments_dict contains: {"buy_orders": float, "sell_orders": float, "oco_orders": float}
        """
        try:
            # Get current account balance
            account_info = self.get_account_info()
            if not account_info:
                logger.error(f"Failed to get account info for {asset} balance check")
                return 0.0, {"buy_orders": 0.0, "sell_orders": 0.0, "oco_orders": 0.0}

            # Find asset balance
            total_balance = 0.0
            for balance in account_info.get("balances", []):
                if balance.get("asset") == asset:
                    total_balance = float(balance.get("free", 0))
                    break

            # Get open orders to calculate commitments
            from .orders import OrderService

            order_service = OrderService(self.client)
            open_orders = order_service.get_open_orders()

            commitments = {"buy_orders": 0.0, "sell_orders": 0.0, "oco_orders": 0.0}

            for order in open_orders:
                # Skip if order doesn't involve our asset
                order_symbol = order.get("symbol", "")

                if asset == "USDT":
                    # For USDT, check buy orders that would consume USDT
                    if order_symbol.endswith("USDT") and order.get("side") == "BUY":
                        try:
                            quantity = float(order.get("origQty", 0))
                            price = float(order.get("price", 0))
                            if price > 0:  # Skip market orders with 0 price
                                commitments["buy_orders"] += quantity * price
                        except (ValueError, TypeError):
                            continue

                else:
                    # For other assets, check sell orders that would consume the asset
                    expected_symbol = f"{asset}USDT"
                    if order_symbol == expected_symbol and order.get("side") == "SELL":
                        try:
                            quantity = float(order.get("origQty", 0))
                            commitments["sell_orders"] += quantity
                        except (ValueError, TypeError):
                            continue

                    # Also check for OCO orders (they consume the asset for sell side)
                    if order_symbol == expected_symbol and order.get("type") == "STOP_LOSS_LIMIT":
                        try:
                            quantity = float(order.get("origQty", 0))
                            commitments["oco_orders"] += quantity
                        except (ValueError, TypeError):
                            continue

            # Calculate effective available balance
            if asset == "USDT":
                available_balance = total_balance - commitments["buy_orders"]
            else:
                available_balance = total_balance - commitments["sell_orders"] - commitments["oco_orders"]

            available_balance = max(0.0, available_balance)  # Ensure non-negative

            logger.debug(f"Effective balance for {asset}: {available_balance} (total: {total_balance}, commitments: {commitments})")
            return available_balance, commitments

        except Exception as e:
            logger.error(f"Error calculating effective available balance for {asset}: {e}")
            return 0.0, {"buy_orders": 0.0, "sell_orders": 0.0, "oco_orders": 0.0}
