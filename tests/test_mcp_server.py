from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# This import must be done before importing the app
# Now import the app from the mcp_server
from mcp_server import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a TestClient instance for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_binance_client() -> Generator[MagicMock, None, None]:
    """Fixture to mock the BinanceClient."""
    with patch("mcp_server.BinanceClient") as mock_client:
        yield mock_client


def test_get_account_info(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_account_service = MagicMock()
    mock_account_service.get_account_info.return_value = {"balances": [], "total_portfolio_value": 0.0}
    with patch("mcp_server.AccountService", return_value=mock_account_service):
        response = client.post("/mcp", json={"action": "get_account_info", "parameters": {}})
        assert response.status_code == 200
        assert response.json() == {"balances": [], "total_portfolio_value": 0.0}


def test_get_account_info_with_min_value(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_account_service = MagicMock()
    mock_account_service.get_account_info.return_value = {
        "balances": [
            {"asset": "BTC", "value_usdt": 100},
            {"asset": "ETH", "value_usdt": 5},
        ],
        "total_portfolio_value": 105,
    }
    with patch("mcp_server.AccountService", return_value=mock_account_service):
        response = client.post("/mcp", json={"action": "get_account_info", "parameters": {"min_value": 10}})
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["balances"]) == 1
        assert response_data["balances"][0]["asset"] == "BTC"
        assert response_data["total_portfolio_value"] == 100


def test_get_account_info_no_total_value_in_response(client: TestClient, mock_binance_client: MagicMock) -> None:
    """Test the case where the account info response does not contain 'total_portfolio_value'."""
    mock_account_service = MagicMock()
    # Return a response without the 'total_portfolio_value' key
    mock_account_service.get_account_info.return_value = {
        "balances": [
            {"asset": "BTC", "value_usdt": 100},
            {"asset": "ETH", "value_usdt": 5},
        ]
    }
    with patch("mcp_server.AccountService", return_value=mock_account_service):
        response = client.post("/mcp", json={"action": "get_account_info", "parameters": {"min_value": 0}})
        assert response.status_code == 200
        response_data = response.json()
        # The server should calculate the total value
        assert response_data["total_portfolio_value"] == 105


def test_get_open_orders(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_order_service = MagicMock()
    mock_order_service.get_open_orders.return_value = [{"orderId": 1}]
    with patch("mcp_server.OrderService", return_value=mock_order_service):
        response = client.post("/mcp", json={"action": "get_open_orders", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 200
        assert response.json() == {"orders": [{"orderId": 1}]}


def test_get_open_orders_api_error(client: TestClient, mock_binance_client: MagicMock) -> None:
    from api.exceptions import BinanceException

    mock_order_service = MagicMock()
    mock_order_service.get_open_orders.side_effect = BinanceException(message="API Error", code=-1001)
    with patch("mcp_server.OrderService", return_value=mock_order_service):
        response = client.post("/mcp", json={"action": "get_open_orders", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]


def test_get_trade_history(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_history_service = MagicMock()
    mock_history_service.get_trade_history.return_value = [{"id": 1}]
    with patch("mcp_server.HistoryService", return_value=mock_history_service):
        response = client.post("/mcp", json={"action": "get_trade_history", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 200
        assert response.json() == {"history": [{"id": 1}]}


def test_get_trade_history_api_error(client: TestClient, mock_binance_client: MagicMock) -> None:
    from api.exceptions import BinanceException

    mock_history_service = MagicMock()
    mock_history_service.get_trade_history.side_effect = BinanceException(message="API Error", code=-1001)
    with patch("mcp_server.HistoryService", return_value=mock_history_service):
        response = client.post("/mcp", json={"action": "get_trade_history", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]


def test_get_trade_history_missing_symbol(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post("/mcp", json={"action": "get_trade_history", "parameters": {}})
    assert response.status_code == 400
    assert "Missing required parameter: symbol" in response.json()["detail"]


def test_get_lot_size_info(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_exchange_service = MagicMock()
    mock_exchange_service.get_lot_size_info.return_value = "0.001"
    with patch("mcp_server.ExchangeService", return_value=mock_exchange_service):
        response = client.post("/mcp", json={"action": "get_lot_size_info", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 200
        assert response.json() == {"stepSize": "0.001"}


def test_get_lot_size_info_missing_symbol(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post("/mcp", json={"action": "get_lot_size_info", "parameters": {}})
    assert response.status_code == 400
    assert "Missing required parameter: symbol" in response.json()["detail"]


def test_get_lot_size_info_api_error(client: TestClient, mock_binance_client: MagicMock) -> None:
    from api.exceptions import BinanceException

    mock_exchange_service = MagicMock()
    mock_exchange_service.get_lot_size_info.side_effect = BinanceException(message="API Error", code=-1001)
    with patch("mcp_server.ExchangeService", return_value=mock_exchange_service):
        response = client.post("/mcp", json={"action": "get_lot_size_info", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]


def test_get_symbol_info(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_exchange_service = MagicMock()
    mock_exchange_service.get_symbol_info.return_value = {"symbol": "BTCUSDT"}
    with patch("mcp_server.ExchangeService", return_value=mock_exchange_service):
        response = client.post("/mcp", json={"action": "get_symbol_info", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 200
        assert response.json() == {"symbol": "BTCUSDT"}


def test_get_symbol_info_missing_symbol(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post("/mcp", json={"action": "get_symbol_info", "parameters": {}})
    assert response.status_code == 400
    assert "Missing required parameter: symbol" in response.json()["detail"]


def test_get_symbol_info_api_error(client: TestClient, mock_binance_client: MagicMock) -> None:
    from api.exceptions import BinanceException

    mock_exchange_service = MagicMock()
    mock_exchange_service.get_symbol_info.side_effect = BinanceException(message="API Error", code=-1001)
    with patch("mcp_server.ExchangeService", return_value=mock_exchange_service):
        response = client.post("/mcp", json={"action": "get_symbol_info", "parameters": {"symbol": "BTCUSDT"}})
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]


def test_get_technical_indicators(client: TestClient, mock_binance_client: MagicMock) -> None:
    # This requires mocking the config as well
    with patch("mcp_server.get_config") as mock_get_config:
        mock_get_config.return_value = {
            "analysis": {
                "ema_periods": [10, 20],
                "rsi_period": 14,
                "min_data_points": 50,
            }
        }
        # Since the service is initialized inside the handler, we mock the service itself
        mock_indicator_service = MagicMock()
        mock_indicator_service.get_technical_indicators.return_value = {"rsi": 50}
        with patch("mcp_server.IndicatorService", return_value=mock_indicator_service):
            response = client.post("/mcp", json={"action": "get_technical_indicators", "parameters": {"coin_symbol": "BTC"}})
            assert response.status_code == 200
            assert response.json() == {"rsi": 50}


def test_get_technical_indicators_missing_symbol(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post("/mcp", json={"action": "get_technical_indicators", "parameters": {}})
    assert response.status_code == 400
    assert "Missing required parameter: coin_symbol" in response.json()["detail"]


def test_get_technical_indicators_api_error(client: TestClient, mock_binance_client: MagicMock) -> None:
    from api.exceptions import BinanceException

    mock_indicator_service = MagicMock()
    mock_indicator_service.get_technical_indicators.side_effect = BinanceException(message="API Error", code=-1001)
    with patch("mcp_server.IndicatorService", return_value=mock_indicator_service):
        with patch("mcp_server.get_config"):  # Also mock config
            response = client.post("/mcp", json={"action": "get_technical_indicators", "parameters": {"coin_symbol": "BTC"}})
            assert response.status_code == 500
            assert "API Error" in response.json()["detail"]


def test_unknown_action(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post("/mcp", json={"action": "unknown_action", "parameters": {}})
    assert response.status_code == 400
    assert "Unknown action: unknown_action" in response.json()["detail"]


def test_binance_client_init_error(client: TestClient) -> None:
    with patch("mcp_server.BinanceClient", side_effect=ValueError("Test Error")):
        response = client.post("/mcp", json={"action": "get_account_info", "parameters": {}})
        assert response.status_code == 500
        assert "Failed to initialize Binance Client: Test Error" in response.json()["detail"]


def test_api_error_handling(client: TestClient, mock_binance_client: MagicMock) -> None:
    from api.exceptions import BinanceException

    mock_account_service = MagicMock()
    mock_account_service.get_account_info.side_effect = BinanceException(message="API Error", code=-1001)
    with patch("mcp_server.AccountService", return_value=mock_account_service):
        response = client.post("/mcp", json={"action": "get_account_info", "parameters": {}})
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]


def test_place_order(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_order_service = MagicMock()
    mock_order_service.place_order.return_value = {"status": "FILLED"}
    with patch("mcp_server.OrderService", return_value=mock_order_service):
        response = client.post(
            "/mcp",
            json={
                "action": "place_order",
                "parameters": {
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "order_type": "MARKET",
                    "quantity": 1,
                },
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "FILLED"}


def test_place_order_missing_params(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post(
        "/mcp",
        json={
            "action": "place_order",
            "parameters": {"symbol": "BTCUSDT"},
        },
    )
    assert response.status_code == 400


def test_cancel_order(client: TestClient, mock_binance_client: MagicMock) -> None:
    mock_order_service = MagicMock()
    mock_order_service.cancel_order.return_value = {"status": "CANCELED"}
    with patch("mcp_server.OrderService", return_value=mock_order_service):
        response = client.post(
            "/mcp",
            json={
                "action": "cancel_order",
                "parameters": {
                    "symbol": "BTCUSDT",
                    "order_type": "LIMIT",
                    "order_id": 123,
                },
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "CANCELED"}


def test_cancel_order_missing_params(client: TestClient, mock_binance_client: MagicMock) -> None:
    response = client.post(
        "/mcp",
        json={
            "action": "cancel_order",
            "parameters": {"symbol": "BTCUSDT"},
        },
    )
    assert response.status_code == 400
