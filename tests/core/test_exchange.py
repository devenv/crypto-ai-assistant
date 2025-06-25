from unittest.mock import MagicMock

import pytest

from core.exchange import ExchangeService


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient."""
    return MagicMock()


@pytest.fixture
def exchange_service(mock_client: MagicMock) -> ExchangeService:
    """Fixture to create an ExchangeService instance with a mock client."""
    return ExchangeService(mock_client)


def test_get_lot_size_info_success(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test successful retrieval of LOT_SIZE stepSize."""
    mock_client.get_exchange_info.return_value = {
        "symbols": [
            {
                "filters": [
                    {"filterType": "PRICE_FILTER"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.00100000"},
                ]
            }
        ]
    }
    step_size = exchange_service.get_lot_size_info("BTCUSDT")
    assert step_size == "0.00100000"
    mock_client.get_exchange_info.assert_called_once_with(symbol="BTCUSDT")


def test_get_lot_size_info_no_info(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test case where exchange info is not available."""
    mock_client.get_exchange_info.return_value = None
    step_size = exchange_service.get_lot_size_info("BTCUSDT")
    assert step_size is None


def test_get_lot_size_info_no_symbol_info(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test case where symbol information is missing."""
    mock_client.get_exchange_info.return_value = {"symbols": []}
    step_size = exchange_service.get_lot_size_info("BTCUSDT")
    assert step_size is None


def test_get_lot_size_info_no_lot_size_filter(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test case where LOT_SIZE filter is not found."""
    mock_client.get_exchange_info.return_value = {
        "symbols": [
            {
                "filters": [
                    {"filterType": "PRICE_FILTER"},
                ]
            }
        ]
    }
    step_size = exchange_service.get_lot_size_info("BTCUSDT")
    assert step_size is None


def test_get_lot_size_info_exception(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test exception handling during API call."""
    mock_client.get_exchange_info.side_effect = Exception("API Error")
    step_size = exchange_service.get_lot_size_info("BTCUSDT")
    assert step_size is None


def test_get_symbol_info_success(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test successful retrieval of symbol info."""
    mock_symbol_info = {"symbol": "BTCUSDT", "status": "TRADING"}
    mock_client.get_exchange_info.return_value = {"symbols": [mock_symbol_info]}
    info = exchange_service.get_symbol_info("BTCUSDT")
    assert info is not None
    assert info["symbol"] == mock_symbol_info["symbol"]
    assert info["status"] == mock_symbol_info["status"]
    mock_client.get_exchange_info.assert_called_once_with(symbol="BTCUSDT")


def test_get_symbol_info_no_info(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test case where exchange info is not available."""
    mock_client.get_exchange_info.return_value = None
    info = exchange_service.get_symbol_info("BTCUSDT")
    assert info is None


def test_get_symbol_info_no_symbol_info(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test case where symbol information is missing."""
    mock_client.get_exchange_info.return_value = {"symbols": []}
    info = exchange_service.get_symbol_info("BTCUSDT")
    assert info is None


def test_get_symbol_info_exception(exchange_service: ExchangeService, mock_client: MagicMock) -> None:
    """Test exception handling during API call."""
    mock_client.get_exchange_info.side_effect = Exception("API Error")
    info = exchange_service.get_symbol_info("BTCUSDT")
    assert info is None
