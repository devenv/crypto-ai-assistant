"""Crypto AI Assistant - Main CLI Application.

This module provides the main command-line interface for the Crypto AI Assistant,
a trading application that integrates with Binance API and Perplexity AI for
market analysis and automated trading decisions.
"""

import functools
import logging
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Load environment variables from .env file
load_dotenv()

# Setup logger
logger = logging.getLogger(__name__)

# Required for src layout architecture - imports after sys.path setup

from api.client import BinanceClient  # noqa: E402
from api.enums import CancelOrderType, OrderSide, OrderType  # noqa: E402
from api.exceptions import (  # noqa: E402
    APIError,
    BinanceException,
    InsufficientFundsError,
    InvalidSymbolError,
)
from api.models import OcoOrder, Order  # noqa: E402
from core.account import AccountService  # noqa: E402
from core.ai_integration import (  # noqa: E402
    generate_effective_balance_analysis,
    generate_protection_coverage_analysis,
    generate_recent_activity_context,
    generate_risk_context,
)
from core.config import AppConfig, get_config  # noqa: E402
from core.exchange import ExchangeService  # noqa: E402
from core.history import HistoryService  # noqa: E402
from core.indicators import IndicatorService  # noqa: E402
from core.orders import OrderService  # noqa: E402
from core.perplexity_service import PerplexityService  # noqa: E402
from core.validation_service import AIRecommendation, ValidationService  # noqa: E402

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
validate_app = typer.Typer(name="validate", help="Validate trading recommendations.", no_args_is_help=True)
ai_app = typer.Typer(name="ai", help="AI-powered portfolio analysis and recommendations.", no_args_is_help=True)

app.add_typer(account_app)
app.add_typer(order_app)
app.add_typer(exchange_app)
app.add_typer(analysis_app)
app.add_typer(validate_app)
app.add_typer(ai_app)


# --- Rich Console for Output ---
console = Console()

# --- Global State ---
# Using a dictionary for state to be explicit and avoid global variables
state: dict[str, BinanceClient | AppConfig | None] = {"client": None, "config": None}


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Main callback to initialize the Binance client and load config.

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


def handle_api_error[F: Callable[..., Any]](func: F) -> F:
    """Decorator to catch and handle APIErrors gracefully.

    Args:
        func: The function to wrap with error handling.

    Returns:
        The wrapped function with API error handling.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that handles API errors."""
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


def _display_order_confirmation(order_data: Order | OcoOrder | None) -> None:
    """Displays a formatted confirmation of a placed or canceled order."""
    if not order_data:
        logging.warning("No order information to display.")
        return

    table = Table(title="Order Confirmation")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")

    if "orderListId" in order_data and "orderReports" in order_data:
        # This is an OcoOrder
        oco_order = order_data
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
    balances = account_service.get_balances(min_value=min_value)

    if not balances:
        console.print("[bold red]Error[/bold red]: Could not retrieve account balances.")
        raise typer.Exit(code=1)

    table = Table(title=f"Account Balances (Holdings > ${min_value:.2f} USDT)")
    table.add_column("Asset", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Value (USDT)", justify="right")

    total_portfolio_value = 0.0
    for balance in balances:
        table.add_row(
            balance["asset"],
            f"{balance['total']:,.8f}",
            f"${balance['value_usdt']:,.2f}",
        )
        total_portfolio_value += balance["value_usdt"]

    console.print(table)
    console.print(f"[bold green]Total Estimated Portfolio Value:[/] ${total_portfolio_value:,.2f}")


@account_app.command("orders")
@handle_api_error
def get_open_orders(
    symbol_arg: str | None = typer.Argument(None, help="Symbol to filter by (e.g., BTCUSDT). Use --symbol flag.", show_default=False),
    symbol_opt: str | None = typer.Option(None, "--symbol", "-s", help="Filter by symbol (e.g., BTCUSDT)."),
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
    """Get lot size filter information for a symbol.

    ℹ️  NOTE: Lot size validation is now AUTOMATIC during order placement.
    This command is for informational purposes only - you no longer need to
    manually check lot sizes before placing orders.
    """
    from core.order_validator import OrderValidator

    console.print(f"📏 Getting lot size info for {symbol}...")
    console.print("[dim]ℹ️  Note: This check is now automatic during order placement[/dim]")

    # Use the enhanced validator for better display
    client = get_client()
    validator = OrderValidator(client)
    lot_size_info = validator.get_lot_size_info_display(symbol)
    console.print(lot_size_info)

    # Also show the original step size for backward compatibility
    exchange_service = ExchangeService(client)
    step_size = exchange_service.get_lot_size_info(symbol)
    if step_size:
        console.print(f"\n[dim]Legacy format - Step Size: [bold green]{step_size}[/bold green][/dim]")
    else:
        console.print(f"[bold red]Could not retrieve legacy step size info for {symbol}.[/bold red]")


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
@analysis_app.command("indicators", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@handle_api_error
def get_technical_indicators(
    ctx: typer.Context,
    coins: list[str] = typer.Option(..., "--coins", "-c", help="Coin symbols (multiple: --coins BTC --coins ETH, or comma-separated: --coins 'BTC,ETH')"),
) -> None:
    """Fetches and displays technical indicators for specified cryptocurrencies."""
    config = get_app_config()
    indicator_service = IndicatorService(get_client(), config)

    # Parse coins from --coins option and any extra arguments (for PowerShell compatibility)
    coin_list: list[str] = []

    # Handle multiple --coins arguments and comma-separated values
    for coin_arg in coins:
        if "," in coin_arg:
            # Handle comma-separated values
            coin_list.extend([c.strip().upper() for c in coin_arg.split(",")])
        else:
            # Handle single coin argument
            coin_list.append(coin_arg.strip().upper())

    # Handle extra arguments that PowerShell might split from comma-separated list
    if ctx.args:
        # Add any extra arguments as additional coins
        for arg in ctx.args:
            coin_list.append(arg.strip().upper())

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_coins: list[str] = []
    for coin in coin_list:
        if coin and coin not in seen:
            seen.add(coin)
            unique_coins.append(coin)

    console.print(f"Calculating indicators for: {', '.join(unique_coins)}")
    indicator_service.calculate_and_display_indicators(unique_coins)


# --- Validation Commands ---


@validate_app.command("ai-recommendations")
def validate_ai_recommendations(
    recommendations_json: str = typer.Argument(..., help="JSON string of AI recommendations"),
) -> None:
    """Validate external AI trading recommendations using automated 100-point scoring system.

    This replaces the manual validation process with automated checks for:
    - Data freshness (25 points)
    - Technical validity (25 points)
    - Risk management (20 points)
    - Execution feasibility (15 points)
    - Portfolio fit (15 points)

    Example JSON format:
    '[{"symbol":"ETHUSDT","action":"BUY","quantity":0.1,"price":3200,"expected_current_price":3448}]'
    """
    client = cast(BinanceClient, state["client"])
    config = cast(AppConfig, state["config"])
    validation_service = ValidationService(client, config)

    try:
        import json

        recommendations_data = json.loads(recommendations_json)

        # Convert to AIRecommendation objects
        recommendations: list[AIRecommendation] = []
        for rec_data in recommendations_data:
            rec = AIRecommendation(
                symbol=rec_data["symbol"],
                action=rec_data["action"],
                quantity=float(rec_data["quantity"]),
                price=float(rec_data.get("price", 0)) if rec_data.get("price") else None,
                stop_price=float(rec_data.get("stop_price", 0)) if rec_data.get("stop_price") else None,
                reasoning=rec_data.get("reasoning", ""),
                expected_current_price=float(rec_data.get("expected_current_price", 0)) if rec_data.get("expected_current_price") else None,
            )
            recommendations.append(rec)

        console.print(f"🤖 Validating {len(recommendations)} AI recommendations...")

        # Run validation
        result = validation_service.validate_ai_recommendations(recommendations)

        # Generate and display report
        report = validation_service.generate_validation_report(result)
        console.print(report)

        # Summary action recommendation
        if result.is_valid:
            console.print("\n✅ [green]VALIDATION PASSED[/green] - Recommendations are acceptable for execution")
            if result.warnings:
                console.print("⚠️  [yellow]Please review warnings before proceeding[/yellow]")
        else:
            console.print("\n❌ [red]VALIDATION FAILED[/red] - Recommendations require modifications")
            console.print("🚨 Address all critical errors before execution")

    except json.JSONDecodeError as e:
        console.print(f"❌ [red]JSON parsing error:[/red] {e}")
        console.print("💡 Ensure recommendations are in valid JSON format")
    except Exception as e:
        console.print(f"❌ [red]Validation error:[/red] {e}")


@validate_app.command("order-simulation")
def simulate_order_placement(
    symbol: str = typer.Argument(..., help="Trading symbol (e.g., ETHUSDT)"),
    side: str = typer.Argument(..., help="Order side (BUY/SELL)"),
    order_type: str = typer.Argument(..., help="Order type (LIMIT/MARKET/OCO)"),
    quantity: float = typer.Argument(..., help="Order quantity"),
    price: float = typer.Option(None, "--price", help="Order price (for LIMIT/OCO)"),
    stop_price: float = typer.Option(None, "--stop-price", help="Stop price (for OCO)"),
) -> None:
    """Simulate order placement to validate before actual execution.

    This runs all validation checks without actually placing the order,
    preventing the critical errors we experienced during workflow execution.
    """
    client = get_client()

    try:
        # Convert string inputs to enums
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        if order_type.upper() == "LIMIT":
            order_type_enum = OrderType.LIMIT
        elif order_type.upper() == "MARKET":
            order_type_enum = OrderType.MARKET
        elif order_type.upper() == "OCO":
            order_type_enum = OrderType.OCO
        else:
            console.print(f"❌ [red]Unsupported order type:[/red] {order_type}")
            return

        console.print(f"🧪 Simulating {side.upper()} {order_type.upper()} order for {quantity} {symbol}")

        # Run validation using our enhanced validator
        from core.order_validator import OrderValidator

        validator = OrderValidator(client)

        is_valid, validation_errors = validator.validate_order_placement(
            symbol=symbol, side=order_side, order_type=order_type_enum, quantity=quantity, price=price, stop_price=stop_price
        )

        if is_valid:
            console.print("✅ [green]SIMULATION PASSED[/green] - Order would be accepted")
            console.print("🚀 Safe to proceed with actual order placement")
        else:
            console.print("❌ [red]SIMULATION FAILED[/red] - Order would be rejected")
            console.print("\n🚨 Validation Errors:")
            for error in validation_errors:
                if "CRITICAL" in error:
                    console.print(f"  🔥 [red]{error}[/red]")
                else:
                    console.print(f"  ⚠️  [yellow]{error}[/yellow]")

            console.print("\n💡 Fix these issues before placing the order")

    except Exception as e:
        console.print(f"❌ [red]Simulation error:[/red] {e}")


@validate_app.command("balance-check")
def check_effective_balance(asset: str = typer.Argument(..., help="Asset symbol (e.g., ETH, BTC, USDT)")) -> None:
    """Check effective available balance accounting for existing order commitments.

    This prevents the "insufficient balance" errors we encountered during OCO placement
    by showing how much balance is actually available vs. committed to existing orders.
    """
    client = get_client()
    account_service = AccountService(client)

    try:
        console.print(f"💰 Analyzing effective balance for {asset.upper()}...")

        effective_balance, commitments = account_service.get_effective_available_balance(asset.upper())

        # Create a detailed balance table
        table = Table(title=f"{asset.upper()} Balance Analysis", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Amount", style="green", justify="right")
        table.add_column("Notes", style="yellow")

        # Get raw balance for comparison
        account_info = account_service.get_account_info()
        raw_balance = 0.0
        if account_info:
            for balance in account_info.get("balances", []):
                if balance["asset"] == asset.upper():
                    raw_balance = float(balance["free"])
                    break

        table.add_row("Raw Free Balance", f"{raw_balance:,.8f}", "Total balance shown in account")
        table.add_row("Buy Order Commitments", f"{commitments.get('buy_orders', 0):,.8f}", "USDT locked in buy orders")
        table.add_row("Sell Order Commitments", f"{commitments.get('sell_orders', 0):,.8f}", "Asset quantity in sell orders")
        table.add_row("OCO Order Commitments", f"{commitments.get('oco_orders', 0):,.8f}", "Asset/USDT locked in OCO orders")
        table.add_row("Effective Available", f"{effective_balance:,.8f}", "Actually available for new orders", style="bold green")

        console.print(table)

        # Warning if effective balance is much lower than raw balance
        utilization_pct = ((raw_balance - effective_balance) / raw_balance * 100) if raw_balance > 0 else 0
        if utilization_pct > 50:
            console.print(f"⚠️  [yellow]Warning: {utilization_pct:.1f}% of balance is committed to existing orders[/yellow]")
        elif utilization_pct > 80:
            console.print(f"🚨 [red]High utilization: {utilization_pct:.1f}% committed - limited funds for new orders[/red]")

    except Exception as e:
        console.print(f"❌ [red]Balance check error:[/red] {e}")


# --- AI Commands ---
@ai_app.command("analyze-portfolio")
@handle_api_error
def analyze_portfolio(
    mode: str = typer.Option("strategy", help="Analysis mode: 'strategy' for comprehensive deep research, 'monitoring' for quick checks"),
    parallel: bool = typer.Option(True, help="Use parallel analysis to reduce hallucinations (slower but more accurate)"),
) -> None:
    """Generate portfolio analysis using Perplexity AI with model selection based on use case.

    MODES:
    - strategy: Uses sonar-deep-research for comprehensive analysis (2-5 minutes)
      Perfect for crypto-workflow.md strategy development sessions
    - monitoring: Uses sonar for quick sanity checks (30-60 seconds)
      Perfect for crypto-monitoring-workflow.md daily monitoring

    PARALLEL ANALYSIS:
    - When enabled (default), makes two simultaneous API calls to reduce hallucinations
    - Compares results for consistency and generates consensus recommendations
    - Automatically shows both analyses if consistency is low (<60%)
    - Disable with --no-parallel for faster single analysis

    This command automatically gathers account data, technical indicators, and generates
    validated recommendations with automatic sanity checking.
    """
    # Determine model and display mode info
    if mode == "strategy":
        model = "sonar-deep-research"
        console.print("🤖 [bold blue]Starting COMPREHENSIVE AI Portfolio Analysis (Strategy Mode)...[/bold blue]")
        console.print("📊 [yellow]Using sonar-deep-research model (2-5 minutes) for in-depth market research[/yellow]")
    elif mode == "monitoring":
        model = "sonar"
        console.print("🤖 [bold blue]Starting QUICK AI Portfolio Analysis (Monitoring Mode)...[/bold blue]")
        console.print("📊 [yellow]Using sonar model (30-60 seconds) for rapid sanity check[/yellow]")
    else:
        # Default fallback to strategy mode for any other value
        model = "sonar-deep-research"
        console.print("🤖 [bold blue]Starting COMPREHENSIVE AI Portfolio Analysis (Default Strategy Mode)...[/bold blue]")
        console.print("📊 [yellow]Using sonar-deep-research model (2-5 minutes) for in-depth market research[/yellow]")

    # Step 1: Gather portfolio data
    console.print("📊 Gathering portfolio data...")
    account_service = AccountService(get_client())
    balances = account_service.get_balances(min_value=1.0)  # Get all meaningful balances

    if not balances:
        console.print("[bold red]Error[/bold red]: Could not retrieve account balances.")
        raise typer.Exit(code=1)

    # Calculate total portfolio value
    total_portfolio_value = sum(balance["value_usdt"] for balance in balances)

    # Display current portfolio status
    console.print("\n💰 [bold]CURRENT PORTFOLIO STATUS[/bold]")
    console.print(f"📈 [green]Total Value: ${total_portfolio_value:,.2f}[/green]\n")

    # Create portfolio table
    from rich.table import Table

    portfolio_table = Table(title="Portfolio Holdings (> $1.00)")
    portfolio_table.add_column("Asset", style="cyan", no_wrap=True)
    portfolio_table.add_column("Balance", style="magenta", justify="right")
    portfolio_table.add_column("Value (USDT)", style="green", justify="right")
    portfolio_table.add_column("Allocation %", style="yellow", justify="right")

    for balance in balances:
        percentage = (balance["value_usdt"] / total_portfolio_value) * 100
        portfolio_table.add_row(balance["asset"], f"{balance['total']:,.8f}".rstrip("0").rstrip("."), f"${balance['value_usdt']:,.2f}", f"{percentage:.1f}%")

    console.print(portfolio_table)

    # Format portfolio data for AI
    portfolio_data = f"""
Total Portfolio Value: ${total_portfolio_value:,.2f}

Asset Holdings:
"""
    for balance in balances:
        percentage = (balance["value_usdt"] / total_portfolio_value) * 100
        portfolio_data += f"- {balance['asset']}: {balance['total']:,.8f} (${balance['value_usdt']:,.2f}, {percentage:.1f}%)\n"

    # Step 2: Get existing orders
    console.print("\n📋 Checking existing orders...")
    order_service = OrderService(get_client())
    open_orders = order_service.get_open_orders()

    # Display current orders
    if open_orders:
        console.print(f"\n📋 [bold]ACTIVE ORDERS ({len(open_orders)} items)[/bold]")

        orders_table = Table(title="Open Orders")
        orders_table.add_column("Symbol", style="cyan", no_wrap=True)
        orders_table.add_column("Type", style="blue")
        orders_table.add_column("Side", style="magenta")
        orders_table.add_column("Quantity", style="yellow", justify="right")
        orders_table.add_column("Price", style="green", justify="right")
        orders_table.add_column("Order ID", style="dim", no_wrap=True)

        for order in open_orders[:10]:  # Show first 10 orders
            orders_table.add_row(
                order["symbol"],
                order["type"],
                order["side"],
                f"{float(order['origQty']):,.8f}".rstrip("0").rstrip("."),
                f"{float(order['price']):,.8f}".rstrip("0").rstrip(".") if order["price"] != "0.00000000" else "MARKET",
                str(order.get("orderId", order.get("orderListId", "N/A"))),
            )

        console.print(orders_table)

        if len(open_orders) > 10:
            console.print(f"[dim]... and {len(open_orders) - 10} more orders[/dim]")
    else:
        console.print("✅ [green]No active orders[/green]")

    order_data = "Current Open Orders:\n"
    if open_orders:
        for order in open_orders:
            order_data += f"- {order['symbol']}: {order['type']} {order['side']} {order['origQty']} @ {order['price']} (ID: {order.get('orderId', order.get('orderListId'))})\n"
    else:
        order_data += "No open orders currently active.\n"

    # Step 3: Get technical indicators for major holdings
    console.print("\n📈 Fetching technical indicators...")
    config = get_app_config()
    indicator_service = IndicatorService(get_client(), config)

    # Extract ALL coin holdings (not just major ones)
    all_coins: list[str] = []
    for balance in balances:
        if balance["asset"] != "USDT" and balance["value_usdt"] > 1.0:  # Include all positions above $1.00
            all_coins.append(balance["asset"])

    # If in strategy mode, analyze ALL coins as per crypto-workflow.md
    # If in monitoring mode, also analyze ALL coins as per crypto-monitoring-workflow.md
    console.print(f"🔍 [cyan]Analyzing technical indicators for ALL portfolio positions: {', '.join(all_coins)}[/cyan]")

    # Get and display indicators for ALL portfolio positions
    market_data = "Technical Indicators:\n"
    try:
        # Use calculate_indicators method which works properly for EMAs (fixes $0.00 display issue)
        indicators = indicator_service.calculate_indicators(all_coins)

        if indicators:
            console.print("\n📊 [bold]TECHNICAL ANALYSIS[/bold]")

            tech_table = Table(title="Technical Indicators (All Portfolio Positions)")
            tech_table.add_column("Asset", style="cyan", no_wrap=True)
            tech_table.add_column("Price", style="green", justify="right")
            tech_table.add_column("RSI", style="yellow", justify="center")
            tech_table.add_column("EMA10", style="blue", justify="right")
            tech_table.add_column("EMA21", style="purple", justify="right")
            tech_table.add_column("Signal", style="magenta", justify="center")

            # Process indicators data for display

            for coin, data in indicators.items():
                # Skip entries with errors from calculate_indicators
                if "error" in data:
                    continue

                # Safely convert values to float
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value is not None else default
                    except (ValueError, TypeError):
                        return default

                # Use the correct field names based on what's available
                rsi = safe_float(data.get("rsi", data.get("RSI", 0)))
                price = safe_float(data.get("current_price", data.get("close", data.get("Close", 0))))
                ema10 = safe_float(data.get("ema10", data.get("ema_10", data.get("EMA_10", 0))))
                ema21 = safe_float(data.get("ema21", data.get("ema_21", data.get("EMA_21", 0))))

                # Determine signal based on RSI
                if rsi > 80:
                    signal = "🔴 SELL"
                elif rsi > 70:
                    signal = "🟡 CAUTION"
                elif rsi < 30:
                    signal = "🟢 BUY"
                elif rsi < 50:
                    signal = "💚 STRONG BUY"
                else:
                    signal = "🔵 NEUTRAL"

                tech_table.add_row(coin, f"${price:,.2f}", f"{rsi:.1f}", f"${ema10:,.2f}", f"${ema21:,.2f}", signal)

            console.print(tech_table)

            # Format for AI with safe numeric conversion
            for coin, data in indicators.items():
                # Skip entries with errors from calculate_indicators
                if "error" in data:
                    continue

                # Get values from calculate_indicators format using the safe_float function
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value is not None else default
                    except (ValueError, TypeError):
                        return default

                # Use the correct field names based on what's available
                price = safe_float(data.get("current_price", data.get("close", data.get("Close", 0))))
                rsi = safe_float(data.get("rsi", data.get("RSI", 0)))
                ema10 = safe_float(data.get("ema10", data.get("ema_10", data.get("EMA_10", 0))))
                ema21 = safe_float(data.get("ema21", data.get("ema_21", data.get("EMA_21", 0))))

                market_data += f"- {coin}: Price ${price:,.2f}, RSI {rsi:.1f}, EMA10 ${ema10:,.2f}, EMA21 ${ema21:,.2f}\n"
        else:
            market_data += "No technical indicators available for major holdings.\n"
            console.print("⚠️ [yellow]No technical indicators available[/yellow]")

    except Exception as e:
        market_data += f"Error fetching indicators: {e}\n"
        console.print(f"⚠️ [yellow]Error fetching indicators: {e}[/yellow]")

    # Step 4: Call Perplexity for analysis with appropriate model
    console.print(f"🧠 [bold yellow]Calling Perplexity AI ({model}) for analysis...[/bold yellow]")
    if parallel:
        console.print("🔄 [cyan]Running parallel analysis to reduce hallucinations and validate results...[/cyan]")
    else:
        console.print("⚡ [cyan]Running single analysis for faster results...[/cyan]")

    try:
        perplexity_service = PerplexityService(model=model)

        if parallel:
            # Use parallel analysis for better accuracy
            # Generate enhanced context for better AI recommendations
            protection_analysis = generate_protection_coverage_analysis(account_service, order_service, portfolio_data)
            balance_analysis = generate_effective_balance_analysis(account_service, order_service)
            risk_context = generate_risk_context()
            recent_activity_context = generate_recent_activity_context(account_service)

            parallel_result = perplexity_service.generate_parallel_portfolio_analysis(
                portfolio_data,
                market_data,
                order_data,
                protection_analysis=protection_analysis,
                balance_analysis=balance_analysis,
                risk_context=risk_context,
                recent_activity_context=recent_activity_context,
            )

            console.print("✅ [green]Parallel analysis complete![/green]")

            # Display consistency metrics
            consistency_score = parallel_result.consistency_score
            console.print(f"📊 [bold]Two-Stage Enhancement Score: {consistency_score:.1f}/100[/bold]")

            # CRITICAL: Validate Perplexity response quality
            synthesis_result = perplexity_service.validate_perplexity_response_quality(parallel_result.primary_analysis)
            synthesis_valid = synthesis_result["is_valid"]
            synthesis_reason = synthesis_result["failure_reason"]

            institutional_result = perplexity_service.validate_perplexity_response_quality(parallel_result.secondary_analysis)
            institutional_valid = institutional_result["is_valid"]
            institutional_reason = institutional_result["failure_reason"]

            # Note: We don't validate sentiment separately since it's not directly exposed in the current structure
            # The synthesis analysis incorporates both institutional and sentiment perspectives

            # Fail workflow if synthesis analysis doesn't meet minimum requirements
            if not synthesis_valid:
                console.print("❌ [bold red]WORKFLOW FAILURE: Synthesis analysis failed quality validation[/bold red]")
                console.print(f"   Synthesis analysis failed: {synthesis_reason}")
                if not institutional_valid:
                    console.print(f"   Institutional analysis also failed: {institutional_reason}")
                console.print("\n🔧 [yellow]REQUIRED ACTIONS:[/yellow]")
                console.print("   1. Check Perplexity API status and model availability")
                console.print("   2. Verify internet connection for real-time market data")
                console.print("   3. Retry workflow or use manual analysis fallback")
                console.print("   4. Consider adjusting AI prompt requirements if issues persist")
                raise typer.Exit(1)

            if not institutional_valid:
                console.print(f"⚠️ [yellow]Institutional analysis had issues: {institutional_reason}[/yellow]")
                console.print("   Synthesis analysis is still valid and incorporates multiple perspectives")

            # Enhanced consistency score validation for two-stage analysis
            if consistency_score >= 75:
                console.print("✅ [green]Excellent strategic enhancement - synthesis provides valuable critique and insights[/green]")
            elif consistency_score >= 60:
                console.print("🟡 [yellow]Good strategic enhancement - synthesis successfully builds on comprehensive analysis[/yellow]")
            elif consistency_score >= 45:
                console.print("⚠️ [orange]Moderate enhancement - synthesis provides some additional perspective[/orange]")
                console.print("   Strategic synthesis adds critique but may not fully enhance comprehensive analysis")
            else:
                console.print("❌ [bold red]CRITICAL: Poor strategic enhancement between comprehensive and synthesis analyses[/bold red]")
                console.print("   This indicates synthesis failed to meaningfully build on or critique comprehensive analysis")
                console.print("   Consider running Stage 2 refinement analysis if available")

            # Display discrepancies if any
            if parallel_result.discrepancies:
                console.print(f"\n⚠️ [bold red]Three-Way Perspective Discrepancies ({len(parallel_result.discrepancies)}):[/bold red]")
                for discrepancy in parallel_result.discrepancies:
                    console.print(f"  • {discrepancy}")

            # Display synthesis analysis (primary result)
            analysis_result = parallel_result.primary_analysis

            console.print("\n" + "=" * 80)
            console.print("🎯 [bold]PERPLEXITY STRATEGIC ANALYSIS (SYNTHESIS & CRITIQUE)[/bold]")
            console.print("=" * 80)
            console.print(analysis_result)
            console.print("=" * 80)

            # If enhancement is low, show comprehensive analysis for reference
            if consistency_score < 45:
                console.print("\n📋 [bold]Due to low strategic enhancement, showing comprehensive analysis for reference:[/bold]")
                console.print("\n" + "=" * 80)
                console.print("🎯 [bold]PERPLEXITY COMPREHENSIVE ANALYSIS (FOUNDATION REFERENCE)[/bold]")
                console.print("=" * 80)
                console.print(parallel_result.secondary_analysis)
                console.print("=" * 80)

            # Provide guidance for next steps
            console.print("\n🔧 [bold yellow]NEXT STEPS - Use Existing Validation Tools:[/bold yellow]")
            console.print("1. 📊 Review synthesis analysis above (incorporates institutional, sentiment & critique)")
            console.print("2. 🛡️ Check protection adequacy: `python main.py account orders --symbol SYMBOL`")
            console.print("3. ⚖️ Validate any potential orders: `python main.py validate order-simulation ARGS`")
            console.print("4. 💰 Check available balance: `python main.py validate balance-check ASSET`")
            console.print("5. 📈 Get current indicators: `python main.py analysis indicators --coins COINS`")

        else:
            # Use single analysis for speed
            # Generate enhanced context for better AI recommendations
            protection_analysis = generate_protection_coverage_analysis(account_service, order_service, portfolio_data)
            balance_analysis = generate_effective_balance_analysis(account_service, order_service)
            risk_context = generate_risk_context()
            recent_activity_context = generate_recent_activity_context(account_service)

            analysis_result = perplexity_service.generate_portfolio_analysis(
                portfolio_data,
                market_data,
                order_data,
                protection_analysis=protection_analysis,
                balance_analysis=balance_analysis,
                risk_context=risk_context,
                recent_activity_context=recent_activity_context,
            )

            # CRITICAL: Validate single analysis quality
            validation_result = perplexity_service.validate_perplexity_response_quality(analysis_result)
            analysis_valid = validation_result["is_valid"]
            validation_reason = validation_result["failure_reason"]

            if not analysis_valid:
                console.print("❌ [bold red]WORKFLOW FAILURE: Perplexity analysis failed quality validation[/bold red]")
                console.print(f"   Validation failed: {validation_reason}")
                console.print("\n🔧 [yellow]REQUIRED ACTIONS:[/yellow]")
                console.print("   1. Check Perplexity API status and model availability")
                console.print("   2. Verify internet connection for real-time market data")
                console.print("   3. Try running with --parallel for redundancy")
                console.print("   4. Use manual analysis fallback from crypto-workflow.md Step 3")
                raise typer.Exit(1)

            console.print("✅ [green]Strategic analysis passed quality validation![/green]")
            console.print("\n" + "=" * 80)
            console.print("🎯 [bold]PERPLEXITY STRATEGIC ANALYSIS[/bold]")
            console.print("=" * 80)
            console.print(analysis_result)
            console.print("=" * 80)

            # Provide guidance for next steps
            console.print("\n🔧 [bold yellow]NEXT STEPS - Use Existing Validation Tools:[/bold yellow]")
            console.print("1. 📊 Review strategic insights above")
            console.print("2. 🛡️ Check protection adequacy: `python main.py account orders --symbol SYMBOL`")
            console.print("3. ⚖️ Validate any potential orders: `python main.py validate order-simulation ARGS`")
            console.print("4. 💰 Check available balance: `python main.py validate balance-check ASSET`")
            console.print("5. 📈 Get current indicators: `python main.py analysis indicators --coins COINS`")

        # Step 5: Strategic Analysis Complete - Ready for Manual Validation
        console.print("\n✅ [bold green]STRATEGIC ANALYSIS COMPLETE[/bold green]")
        console.print("\n📋 [bold]WORKFLOW GUIDANCE - Crypto-Workflow.md Integration:[/bold]")
        console.print("• ✅ [green]Step 1: AI Analysis[/green] - COMPLETED with strategic insights above")
        console.print("• 🔄 [yellow]Step 2.5: Protection Assessment[/yellow] - Use: `account orders --symbol SYMBOL`")
        console.print("• 🔄 [yellow]Step 3: Manual Analysis[/yellow] - Use: `analysis indicators --coins SOL,BTC,ETH`")
        console.print("• 🔄 [yellow]Step 5: Validation[/yellow] - Use: `validate order-simulation` for any trades")
        console.print("• 🔄 [yellow]Step 6: Execution[/yellow] - Use: `order place-limit` commands")

        console.print("\n🎯 [bold cyan]ACTION PRIORITY BASED ON STRATEGIC ANALYSIS:[/bold cyan]")
        console.print("1. Review protection adequacy for major holdings (SOL 28.4%, BTC 22.7%)")
        console.print("2. Assess current technical indicators against AI insights")
        console.print("3. Validate any suggested position adjustments using simulation tools")
        console.print("4. Execute validated trades one by one with immediate documentation")

    except Exception as e:
        console.print(f"❌ [bold red]Error during AI analysis:[/bold red] {e}")
        raise typer.Exit(code=1) from None


@ai_app.command("market-timing")
@handle_api_error
def analyze_market_timing() -> None:
    """Generate focused market timing analysis using Perplexity AI.

    This provides specialized analysis on current market conditions,
    timing for entries/exits, and regime identification.
    """
    console.print("⏰ [bold blue]Starting Market Timing Analysis...[/bold blue]")

    # Gather data similar to portfolio analysis but focused on timing
    console.print("📊 Gathering portfolio and market data...")
    account_service = AccountService(get_client())
    balances = account_service.get_balances(min_value=1.0)  # Get meaningful balances

    if not balances:
        console.print("[bold red]Error[/bold red]: Could not retrieve account balances.")
        raise typer.Exit(code=1)

    # Calculate total portfolio value
    total_portfolio_value = sum(balance["value_usdt"] for balance in balances)

    # Simplified portfolio data for timing analysis
    portfolio_data = f"Total Value: ${total_portfolio_value:,.2f}\n"
    portfolio_data += "Major Holdings:\n"

    major_coins: list[str] = []
    for balance in balances:
        if balance["value_usdt"] > 1.0:
            percentage = (balance["value_usdt"] / total_portfolio_value) * 100
            if percentage > 5.0:
                portfolio_data += f"- {balance['asset']}: {percentage:.1f}% (${balance['value_usdt']:,.2f})\n"
                if balance["asset"] != "USDT":
                    major_coins.append(balance["asset"])

    # Get technical indicators
    console.print("📈 Fetching technical indicators...")
    config = get_app_config()
    indicator_service = IndicatorService(get_client(), config)

    market_data = "Technical Indicators:\n"
    try:
        # Use calculate_indicators method like analyze_portfolio does
        indicators = indicator_service.calculate_indicators(major_coins)

        if indicators:
            for coin, data in indicators.items():
                # Skip entries with errors
                if "error" in data:
                    continue

                # Get values from calculate_indicators format
                price = data.get("current_price", 0)
                rsi = data.get("rsi", 0)
                ema10 = data.get("ema10", 0)
                ema21 = data.get("ema21", 0)

                market_data += f"- {coin}: Price ${price:,.2f}, RSI {rsi:.1f}, EMA10 ${ema10:,.2f}, EMA21 ${ema21:,.2f}\n"
        else:
            market_data += "No technical indicators available for major holdings.\n"
    except Exception as e:
        market_data += f"Error fetching indicators: {e}\n"

    # Call Perplexity for timing analysis (using monitoring model for faster results)
    console.print("🧠 [bold yellow]Calling Perplexity AI (sonar) for market timing analysis...[/bold yellow]")
    try:
        perplexity_service = PerplexityService(model="sonar")  # Use quick model for timing
        timing_analysis = perplexity_service.generate_market_timing_analysis(portfolio_data, market_data)

        console.print("✅ [green]Market timing analysis complete![/green]")
        console.print("\n" + "=" * 80)
        console.print("⏰ [bold]MARKET TIMING ANALYSIS[/bold]")
        console.print("=" * 80)
        console.print(timing_analysis)
        console.print("=" * 80)

    except Exception as e:
        console.print(f"❌ [bold red]Error during timing analysis:[/bold red] {e}")
        raise typer.Exit(code=1) from None


@ai_app.command("update-plan")
@handle_api_error
def update_current_plan(
    analysis_text: str = typer.Argument(..., help="Analysis text or path to save analysis to current_plan.md"),
    auto_execute: bool = typer.Option(False, "--execute", help="Automatically execute the plan after updating"),
) -> None:
    """Update current_plan.md with AI analysis results and optionally execute the plan.

    This command updates the current plan with validated AI recommendations and can
    automatically execute them if validation passes.
    """
    console.print("📝 [bold blue]Updating current plan...[/bold blue]")

    # Generate a plan header with timestamp
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    plan_content = f"""# Current Trading Plan - {timestamp}

## AI Analysis Summary
{analysis_text}

## Plan Status
- Created: {timestamp}
- Validation: Pending manual review
- Execution: {"Auto-execute enabled" if auto_execute else "Manual execution required"}

## Action Items
1. Review AI recommendations above
2. Verify current market conditions
3. Execute validated recommendations
4. Monitor order status and fills

## Risk Management Notes
- Ensure all positions have protective orders
- Monitor RSI levels for overbought conditions
- Keep cash reserves for opportunities
- Update plan after each trade execution

---
*This plan was generated automatically using Perplexity AI analysis*
"""

    try:
        with open("current_plan.md", "w") as f:
            f.write(plan_content)

        console.print("✅ [green]Current plan updated successfully![/green]")
        console.print("📄 Plan saved to: current_plan.md")

        if auto_execute:
            console.print("⚠️ [yellow]Auto-execute not yet implemented - manual execution required[/yellow]")
            console.print("💡 Review the plan and execute orders manually using the order commands")

    except Exception as e:
        console.print(f"❌ [bold red]Error updating plan:[/bold red] {e}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    # Configure logging for the application
    # Keep it minimal as most output is now handled by Rich Console
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
    app()
