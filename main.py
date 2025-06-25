import functools
import logging
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, Union, cast

import typer
from rich.console import Console
from rich.table import Table

from api.client import BinanceClient
from api.enums import CancelOrderType, OrderSide, OrderType
from api.exceptions import APIError, BinanceException, InsufficientFundsError, InvalidSymbolError
from api.models import OcoOrder, Order
from core.account import AccountService
from core.config import AppConfig, get_config
from core.exchange import ExchangeService
from core.history import HistoryService
from core.indicators import IndicatorService
from core.orders import OrderService

# --- Main Typer App ---
app = typer.Typer(
    name="crypto-ai-assistant",
    help="A command-line interface for the Crypto AI Assistant.",
    no_args_is_help=True,
)

# --- Sub-Apps for Organization ---
account_app = typer.Typer(name="account", help="Manage account information.", no_args_is_help=True)
order_app = typer.Typer(name="order", help="Place and cancel orders.", no_args_is_help=True)
exchange_app = typer.Typer(name="exchange", help="Get exchange information.", no_args_is_help=True)
analysis_app = typer.Typer(name="analysis", help="Run technical analysis.", no_args_is_help=True)

app.add_typer(account_app)
app.add_typer(order_app)
app.add_typer(exchange_app)
app.add_typer(analysis_app)


# --- Rich Console for Output ---
console = Console()

# --- Global State ---
# Using a dictionary for state to be explicit and avoid global variables
state: dict[str, BinanceClient | AppConfig | None] = {"client": None, "config": None}


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """
    Main callback to initialize the Binance client and load config.
    This runs before any command.
    """
    if ctx.invoked_subcommand is None:
        return

    # Load configuration once
    if state["config"] is None:
        try:
            state["config"] = get_config()
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]Error[/bold red]: {e}")
            raise typer.Exit(code=1) from e

    # Initialize the Binance client once and store it in the state
    if state["client"] is None:
        try:
            state["client"] = BinanceClient()
        except ValueError as e:
            console.print(f"[bold red]Error[/bold red]: Failed to initialize Binance Client: {e}")
            raise typer.Exit(code=1) from e


# --- Helper to get client ---
def get_client() -> BinanceClient:
    """Gets the initialized BinanceClient from state."""
    client = state["client"]
    if client is None:
        # This should not happen if the callback is configured correctly
        console.print("[bold red]Error[/bold red]: Client not initialized.")
        raise typer.Exit(code=1)
    return cast(BinanceClient, client)


def get_app_config() -> AppConfig:
    """Gets the application config from state."""
    config = state["config"]
    if config is None:
        # This should not happen if the callback is configured correctly
        console.print("[bold red]Error[/bold red]: Config not loaded.")
        raise typer.Exit(code=1)
    return cast(AppConfig, config)


F = TypeVar("F", bound=Callable[..., Any])


def handle_api_error(func: F) -> F:
    """Decorator to catch and handle APIErrors gracefully."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except InvalidSymbolError as e:
            console.print(f"[bold red]Error[/bold red]: Invalid Symbol. {e}")
            raise typer.Exit(code=1) from e
        except InsufficientFundsError as e:
            console.print(f"[bold red]Error[/bold red]: Insufficient funds. {e}")
            raise typer.Exit(code=1) from e
        except BinanceException as e:
            console.print(f"[bold red]Binance API Error[/bold red]: {e}")
            raise typer.Exit(code=1) from e
        except APIError as e:
            console.print(f"[bold red]API Error[/bold red]: {e}")
            raise typer.Exit(code=1) from e

    return cast(F, wrapper)


def _display_order_confirmation(order_data: Optional[Union[Order, OcoOrder]]) -> None:
    """Displays a formatted confirmation of a placed or canceled order."""
    if not order_data:
        logging.warning("No order information to display.")
        return

    table = Table(title="Order Confirmation")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")

    if "orderListId" in order_data and "orderReports" in order_data:
        # This is an OcoOrder
        oco_order = cast(OcoOrder, order_data)
        table.add_row("Symbol", oco_order.get("symbol"))
        table.add_row("Order List ID", str(oco_order.get("orderListId")))
        table.add_row("Overall Status", f"[green]{oco_order.get('listOrderStatus')}[/green]")
        console.print(table)

        report_table = Table(title="Detailed Order Reports", show_header=True, header_style="bold magenta")
        report_table.add_column("Order ID")
        report_table.add_column("Status")
        report_table.add_column("Type")
        report_table.add_column("Side")
        report_table.add_column("Price")
        report_table.add_column("Stop Price")

        for report in oco_order["orderReports"]:
            report_table.add_row(
                str(report.get("orderId")),
                f"[green]{report.get('status')}[/green]",
                report.get("type"),
                report.get("side"),
                report.get("price"),
                report.get("stopPrice", "N/A"),
            )
        console.print(report_table)
    elif "orderId" in order_data:
        # This is a standard Order
        order = order_data
        table.add_row("Symbol", order.get("symbol"))
        table.add_row("Order ID", str(order.get("orderId")))
        table.add_row("Status", f"[green]{order.get('status')}[/green]")
        table.add_row("Type", order.get("type"))
        table.add_row("Side", order.get("side"))
        table.add_row("Price", order.get("price"))
        table.add_row("Quantity", order.get("origQty"))
        console.print(table)
    else:
        # Fallback for any other format
        console.print(order_data)


# --- Account Commands ---
@account_app.command("info")
@handle_api_error
def get_account_info(
    min_value: float = typer.Option(
        lambda: get_app_config()["cli"]["account_min_value"],
        "--min-value",
        "-v",
        help="Minimum USDT value to display an asset.",
    ),
) -> None:
    """Get account balance and value information."""
    console.print("Fetching account information...")
    account_service = AccountService(get_client())
    info = account_service.get_account_info()

    if not info:
        console.print("[bold red]Error[/bold red]: Could not retrieve account info.")
        raise typer.Exit(code=1)

    table = Table(title=f"Account Balances (Holdings > ${min_value:.2f} USDT)")
    table.add_column("Asset", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Value (USDT)", justify="right")

    for balance in info["balances"]:
        if balance["value_usdt"] > min_value:
            table.add_row(
                balance["asset"],
                f"{balance['total']:,.8f}",
                f"${balance['value_usdt']:,.2f}",
            )

    console.print(table)
    console.print(f"[bold green]Total Estimated Portfolio Value:[/] ${info['total_portfolio_value']:,.2f}")


@account_app.command("orders")
@handle_api_error
def get_open_orders(
    symbol_arg: Optional[str] = typer.Argument(None, help="Symbol to filter by (e.g., BTCUSDT). Use --symbol flag.", show_default=False),
    symbol_opt: Optional[str] = typer.Option(None, "--symbol", "-s", help="Filter by symbol (e.g., BTCUSDT)."),
) -> None:
    """Get all open orders."""
    # Combine and validate symbol inputs
    if symbol_arg and symbol_opt:
        console.print("[bold red]Error:[/bold red] Please provide the symbol using either the positional argument or the --symbol option, not both.")
        raise typer.Exit(code=1)

    symbol = symbol_arg or symbol_opt

    console.print(f"Fetching open orders for symbol: {symbol or 'All'}...")
    order_service = OrderService(get_client())
    open_orders = order_service.get_open_orders(symbol)

    if not open_orders:
        if symbol:
            console.print(f"[yellow]No open orders found for symbol {symbol}.[/yellow]")
        else:
            console.print("[yellow]No open orders found.[/yellow]")
        return

    table = Table(title="Open Orders")
    table.add_column("Time", style="magenta", no_wrap=True)
    table.add_column("Symbol", style="cyan")
    table.add_column("ID", justify="right", no_wrap=True)
    table.add_column("List ID", justify="right", no_wrap=True)
    table.add_column("Type", style="yellow")
    table.add_column("Side", style="bold")
    table.add_column("Price", justify="right")
    table.add_column("Quantity", justify="right")
    table.add_column("Status", style="green")

    for order in open_orders:
        order_time = datetime.fromtimestamp(order["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        side_style = "bold green" if order["side"] == "BUY" else "bold red"
        table.add_row(
            order_time,
            order["symbol"],
            str(order.get("orderId", "N/A")),
            str(order.get("orderListId", "N/A")),
            order["type"],
            f"[{side_style}]{order['side']}[/]",
            f"{float(order['price']):,.8f}",
            f"{float(order['origQty']):,.8f}",
            f"[green]{order['status']}[/green]",
        )
    console.print(table)


@account_app.command("history")
@handle_api_error
def get_trade_history(
    symbol: str = typer.Argument(..., help="The symbol to get history for (e.g., BTCUSDT)."),
    limit: int = typer.Option(
        lambda: get_app_config()["cli"]["history_limit"],
        "--limit",
        "-l",
        help="Number of trades to retrieve.",
    ),
) -> None:
    """Get trade history for a specific symbol."""
    console.print(f"Fetching last {limit} trades for symbol: {symbol}...")
    history_service = HistoryService(get_client())
    trades = history_service.get_trade_history(symbol, limit)

    if not trades:
        console.print(f"[yellow]No trade history found for {symbol}.[/yellow]")
        return

    table = Table(title=f"Trade History for {symbol}")
    table.add_column("Time", style="magenta")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Quantity", justify="right")
    table.add_column("Commission", justify="right")

    for trade in trades:
        trade_time = datetime.fromtimestamp(trade["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(
            trade_time,
            f"{float(trade['price']):.4f}",
            f"{float(trade['qty']):.8f}",
            f"{trade['commission']} {trade['commissionAsset']}",
        )
    console.print(table)


# --- Order Commands ---
@order_app.command("place-market")
@handle_api_error
def place_market_order(
    symbol: str = typer.Argument(..., help="Symbol (e.g., BTCUSDT)"),
    side: OrderSide = typer.Argument(..., help="Side: BUY or SELL", case_sensitive=False),
    quantity: float = typer.Argument(..., help="Quantity to trade"),
) -> None:
    """Place a MARKET order."""
    order_service = OrderService(get_client())
    console.print(f"Placing MARKET {side.value.upper()} order for {quantity} {symbol}...")
    result = order_service.place_order(symbol, side, OrderType.MARKET, quantity)
    if result:
        _display_order_confirmation(result)


@order_app.command("place-limit")
@handle_api_error
def place_limit_order(
    symbol: str = typer.Argument(..., help="Symbol (e.g., BTCUSDT)"),
    side: OrderSide = typer.Argument(..., help="Side: BUY or SELL", case_sensitive=False),
    quantity: float = typer.Argument(..., help="Quantity to trade"),
    price: float = typer.Argument(..., help="Price to trade at"),
) -> None:
    """Place a LIMIT order."""
    order_service = OrderService(get_client())
    console.print(f"Placing LIMIT {side.value.upper()} order for {quantity} {symbol} at ${price:,.4f}...")
    result = order_service.place_order(symbol, side, OrderType.LIMIT, quantity, price)
    if result:
        _display_order_confirmation(result)


@order_app.command("place-oco")
@handle_api_error
def place_oco_order(
    symbol: str = typer.Argument(..., help="Symbol (e.g., BTCUSDT)"),
    quantity: float = typer.Argument(..., help="Quantity to sell"),
    price: float = typer.Argument(..., help="The limit price for the OCO order (take-profit)."),
    stop_price: float = typer.Argument(..., help="The stop price for the OCO order (stop-loss)."),
) -> None:
    """Place a One-Cancels-the-Other (OCO) SELL order."""
    order_service = OrderService(get_client())
    side = OrderSide.SELL
    console.print(f"Placing OCO {side.value.upper()} order for {quantity} {symbol} with price ${price:,.4f} and stop ${stop_price:,.4f}...")
    result = order_service.place_order(symbol, side, OrderType.OCO, quantity, price, stop_price)
    if result:
        _display_order_confirmation(result)


@order_app.command("cancel")
@handle_api_error
def cancel_order(
    cancel_type_arg: CancelOrderType = typer.Argument(..., help="Type of order to cancel: 'order' or 'oco'", case_sensitive=False),
    symbol: str = typer.Argument(..., help="The trading symbol (e.g., BTCUSDT)"),
    order_id: int = typer.Argument(..., help="The orderId or orderListId to cancel"),
) -> None:
    """Cancel an active order or OCO order."""
    order_service = OrderService(get_client())
    console.print(f"Attempting to cancel {cancel_type_arg.value.upper()} order {order_id} on {symbol}...")

    # Map the user-friendly cancel type to the required OrderType for the service
    order_type_to_cancel = OrderType.OCO if cancel_type_arg == CancelOrderType.OCO else OrderType.LIMIT

    if order_type_to_cancel == OrderType.OCO:
        result = order_service.cancel_order(order_type_to_cancel, symbol, order_list_id=order_id)
    else:
        result = order_service.cancel_order(order_type_to_cancel, symbol, order_id=order_id)

    if result:
        _display_order_confirmation(result)


# --- Exchange Commands ---
@exchange_app.command("lotsize")
@handle_api_error
def get_lot_size_info(symbol: str = typer.Argument(..., help="Symbol (e.g., BTCUSDT)")) -> None:
    """Get lot size filter information for a symbol."""
    console.print(f"Fetching lot size info for {symbol}...")
    exchange_service = ExchangeService(get_client())
    step_size = exchange_service.get_lot_size_info(symbol)
    if step_size:
        console.print(f"Step Size for {symbol}: [bold green]{step_size}[/bold green]")
    else:
        console.print(f"[bold red]Could not retrieve lot size info for {symbol}.[/bold red]")


@exchange_app.command("info")
@handle_api_error
def get_exchange_info(symbol: str = typer.Argument(..., help="Symbol (e.g., BTCUSDT)")) -> None:
    """Get all exchange filters for a symbol."""
    console.print(f"Fetching exchange info for {symbol}...")
    exchange_service = ExchangeService(get_client())
    info = exchange_service.get_symbol_info(symbol)

    if not info:
        console.print(f"[bold red]Could not retrieve exchange info for {symbol}.[/bold red]")
        raise typer.Exit(code=1)

    table = Table(title=f"Exchange Filters for {symbol}")
    table.add_column("Filter Type", style="cyan", no_wrap=True)
    table.add_column("Parameters", style="bold")

    for f in info.get("filters", []):
        filter_type = f.get("filterType")
        params = ", ".join([f"{k}={v}" for k, v in f.items() if k != "filterType"])
        table.add_row(filter_type, params)

    console.print(table)


# --- Analysis Commands ---
@analysis_app.command("indicators")
@handle_api_error
def get_technical_indicators(coins: str = typer.Option(..., "--coins", "-c", help="Comma-separated list of coin symbols (e.g., BTC,ETH)")) -> None:
    """Fetches and displays technical indicators for specified cryptocurrencies."""
    config = get_app_config()
    indicator_service = IndicatorService(get_client(), config)
    coin_list = [c.strip().upper() for c in coins.split(",")]
    console.print(f"Calculating indicators for: {', '.join(coin_list)}")
    indicator_service.calculate_and_display_indicators(coin_list)


if __name__ == "__main__":
    # Configure logging for the application
    # Keep it minimal as most output is now handled by Rich Console
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
    app()
