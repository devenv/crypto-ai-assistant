from unittest.mock import MagicMock

import pytest

from core.history import HistoryService


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient."""
    return MagicMock()


@pytest.fixture
def history_service(mock_client: MagicMock) -> HistoryService:
    """Fixture to create a HistoryService instance with a mock client."""
    return HistoryService(mock_client)


def test_get_trade_history_success(history_service: HistoryService, mock_client: MagicMock) -> None:
    """Test successful retrieval of trade history."""
    mock_trades = [
        {"symbol": "BTCUSDT", "id": 1, "orderId": 100, "price": "50000", "time": 1617225600000},
        {"symbol": "BTCUSDT", "id": 2, "orderId": 101, "price": "50001", "time": 1617225700000},
    ]
    mock_client.get_trade_history.return_value = mock_trades

    trades = history_service.get_trade_history("BTCUSDT", limit=2)

    assert len(trades) == 2
    assert trades == mock_trades
    mock_client.get_trade_history.assert_called_once_with(symbol="BTCUSDT", limit=2)


def test_get_trade_history_no_trades(history_service: HistoryService, mock_client: MagicMock) -> None:
    """Test the case where no trade history is found."""
    mock_client.get_trade_history.return_value = []

    trades = history_service.get_trade_history("BTCUSDT")

    assert len(trades) == 0
    mock_client.get_trade_history.assert_called_once_with(symbol="BTCUSDT", limit=10)
