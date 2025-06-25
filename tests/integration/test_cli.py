# NOTE: These integration tests are currently failing due to issues with the
# test runner and mocking setup. The exit codes are not being correctly
# reported, and the mocked data is not consistently being passed to the
# application commands. These tests are marked as xfail to prevent them
# from blocking the build, but they need to be fixed.

from typing import cast
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from main import app
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from api.exceptions import BinanceException

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_main_state() -> None:
    """Reset the state in main.py before each test."""
    from main import state

    state["client"] = None
    state["config"] = None


@pytest.fixture
def mock_binance_client(mocker: MockerFixture) -> MagicMock:
    """Fixture to mock the BinanceClient."""
    return cast(MagicMock, mocker.patch("main.BinanceClient"))


def test_account_info_success(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'account info' command with a successful API response."""
    mock_instance = mock_binance_client.return_value
    mock_instance.get_account_info.return_value = {
        "balances": [
            {"asset": "BTC", "free": "1.0", "locked": "0.0"},
            {"asset": "ETH", "free": "10.0", "locked": "0.5"},
        ],
        "canTrade": True,
    }
    mock_instance.get_all_tickers.return_value = [
        {"symbol": "BTCUSDT", "price": "60000.0"},
        {"symbol": "ETHUSDT", "price": "3000.0"},
    ]
    result = runner.invoke(app, ["account", "info", "--min-value", "100"])
    assert result.exit_code == 0
    assert "BTC" in result.stdout
    assert "60,000.00" in result.stdout
    assert "ETH" in result.stdout
    assert "31,500.00" in result.stdout
    assert "Total Estimated Portfolio Value" in result.stdout


def test_account_info_api_error(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'account info' command when the API returns an error."""
    mock_instance = mock_binance_client.return_value
    mock_instance.get_account_info.side_effect = BinanceException("API Error", code=-1000)
    mock_instance.get_all_tickers.return_value = [{"symbol": "BTCUSDT", "price": "60000.0"}]

    result = runner.invoke(app, ["account", "info"])
    assert result.exit_code == 1, result.stdout
    assert "Binance API Error" in result.stdout
    assert "API Error" in result.stdout


def test_get_open_orders_success(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'account orders' command with a successful response."""
    mock_instance = mock_binance_client.return_value
    mock_instance.get_open_orders.return_value = [
        {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "time": 1622548800000,
            "type": "LIMIT",
            "side": "BUY",
            "price": "60000.0",
            "origQty": "1.00000000",
            "status": "NEW",
        }
    ]
    result = runner.invoke(app, ["account", "orders", "--symbol", "BTCUSDT"])
    assert result.exit_code == 0, result.stdout
    assert "12345" in result.stdout


def test_get_open_orders_empty(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'account orders' command when there are no open orders."""
    mock_instance = mock_binance_client.return_value
    mock_instance.get_open_orders.return_value = []
    result = runner.invoke(app, ["account", "orders", "--symbol", "BTCUSDT"])
    assert result.exit_code == 0, result.stdout
    assert "No open orders found" in result.stdout


def test_get_trade_history_success(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'account history' command with a successful response."""
    mock_instance = mock_binance_client.return_value
    mock_instance.get_trade_history.return_value = [
        {
            "time": 1622548800000,
            "price": "59000.0",
            "qty": "0.5",
            "commission": "0.0005",
            "commissionAsset": "BNB",
        }
    ]
    result = runner.invoke(app, ["account", "history", "BTCUSDT"])
    assert result.exit_code == 0, result.stdout
    assert "59000.0" in result.stdout


def test_get_trade_history_empty(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'account history' command when there is no trade history."""
    mock_instance = mock_binance_client.return_value
    mock_instance.get_trade_history.return_value = []
    result = runner.invoke(app, ["account", "history", "BTCUSDT"])
    assert result.exit_code == 0, result.stdout
    assert "No trade history found" in result.stdout


def test_place_order_success(mock_binance_client: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """Test the 'exchange place-order' command with a successful response."""
    mock_instance = mock_binance_client.return_value
    mock_instance.place_limit_order.return_value = {
        "symbol": "BTCUSDT",
        "orderId": 12345,
        "transactTime": 1622548800000,
        "price": "60000.0",
        "origQty": "1.0",
        "status": "FILLED",
    }
    result = runner.invoke(
        app,
        [
            "order",
            "place-limit",
            "BTCUSDT",
            "buy",
            "1.0",
            "60000.0",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Order Confirmation" in result.stdout
    assert "BTCUSDT" in result.stdout
    assert "12345" in result.stdout
