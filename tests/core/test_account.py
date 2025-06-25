import sys
from unittest.mock import MagicMock

import pytest

from core.account import AccountService

sys.path.append("src")


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient."""
    mock = MagicMock()
    mock.get_account_info.return_value = {
        "balances": [
            {"asset": "BTC", "free": "1.0", "locked": "0.5"},
            {"asset": "ETH", "free": "10.0", "locked": "0.0"},
            {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
            {"asset": "XRP", "free": "100.0", "locked": "0.0"},  # No USDT pair
            {"asset": "LTC", "free": "0.0", "locked": "0.0"},  # Zero balance
        ]
    }
    mock.get_all_tickers.return_value = [
        {"symbol": "BTCUSDT", "price": "50000.0"},
        {"symbol": "ETHUSDT", "price": "3000.0"},
    ]
    return mock


@pytest.fixture
def account_service(mock_client: MagicMock) -> AccountService:
    """Fixture to create an AccountService instance with a mock client."""
    return AccountService(mock_client)


def test_get_account_info_success(account_service: AccountService, mock_client: MagicMock) -> None:
    """Test successful processing of account info."""
    result = account_service.get_account_info()
    assert result is not None
    assert "balances" in result
    assert "total_portfolio_value" in result

    # Check total value
    assert result["total_portfolio_value"] == pytest.approx(106000.0)

    # Check specific asset values
    balances_map = {b["asset"]: b for b in result["balances"]}
    assert balances_map["BTC"]["value_usdt"] == pytest.approx(75000.0)
    assert balances_map["ETH"]["value_usdt"] == pytest.approx(30000.0)
    assert balances_map["USDT"]["value_usdt"] == pytest.approx(1000.0)
    assert balances_map["XRP"]["value_usdt"] == 0  # No price, so value is 0


def test_get_account_info_api_failure(account_service: AccountService, mock_client: MagicMock) -> None:
    """Test handling of API failure when getting account info."""
    mock_client.get_account_info.return_value = None  # Simulate failure
    result = account_service.get_account_info()
    assert result is None


def test_get_account_info_general_exception(account_service: AccountService, mock_client: MagicMock) -> None:
    """Test handling of a general exception during processing."""
    mock_client.get_all_tickers.side_effect = Exception("Test exception")
    result = account_service.get_account_info()
    assert result is None
