import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.client import BinanceClient
from api.exceptions import APIError, BinanceException
from core.account import AccountService
from core.config import get_config
from core.exchange import ExchangeService
from core.history import HistoryService
from core.indicators import IndicatorService
from core.orders import OrderService

app = FastAPI()

logging.basicConfig(level=logging.INFO)


class McpRequest(BaseModel):
    action: str
    parameters: dict[str, Any]


@app.post("/mcp")
async def handle_mcp_request(request: McpRequest) -> dict[str, Any]:
    # This is a simplified client and service initialization for now.
    # We might want to use a dependency injection system later.
    logging.info(f"Received MCP request: {request.dict()}")
    try:
        client = BinanceClient()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Binance Client: {e}") from e

    action = request.action
    parameters = request.parameters

    if action == "get_account_info":
        try:
            account_service = AccountService(client)
            info = account_service.get_account_info()

            if info and "balances" in info:
                min_value = parameters.get("min_value", 0.0)
                if min_value > 0.0:
                    filtered_balances = [b for b in info["balances"] if b.get("value_usdt", 0) > min_value]
                    info["balances"] = filtered_balances
                    info["total_portfolio_value"] = sum(b.get("value_usdt", 0) for b in filtered_balances)
                elif "total_portfolio_value" not in info:
                    info["total_portfolio_value"] = sum(b.get("value_usdt", 0) for b in info["balances"])

            logging.info(f"Returning account info: {info}")
            return info or {}
        except (BinanceException, APIError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "get_open_orders":
        try:
            order_service = OrderService(client)
            symbol = parameters.get("symbol")
            open_orders = order_service.get_open_orders(symbol=symbol)
            logging.info(f"Returning open orders: {open_orders}")
            return {"orders": open_orders}
        except (BinanceException, APIError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "get_trade_history":
        try:
            history_service = HistoryService(client)
            symbol = parameters.get("symbol")
            if not symbol:
                raise HTTPException(status_code=400, detail="Missing required parameter: symbol")

            limit = parameters.get("limit", 10)
            trade_history = history_service.get_trade_history(symbol=symbol, limit=limit)
            logging.info(f"Returning trade history: {trade_history}")
            return {"history": trade_history}
        except (BinanceException, APIError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "get_lot_size_info":
        try:
            exchange_service = ExchangeService(client)
            symbol = parameters.get("symbol")
            if not symbol:
                raise HTTPException(status_code=400, detail="Missing required parameter: symbol")

            lot_size_info = exchange_service.get_lot_size_info(symbol=symbol)
            logging.info(f"Returning lot size info: {{'stepSize': '{lot_size_info}'}}")
            return {"stepSize": lot_size_info}
        except (BinanceException, APIError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "get_symbol_info":
        try:
            exchange_service = ExchangeService(client)
            symbol = parameters.get("symbol")
            if not symbol:
                raise HTTPException(status_code=400, detail="Missing required parameter: symbol")

            symbol_info = exchange_service.get_symbol_info(symbol=symbol)
            logging.info(f"Returning symbol info: {symbol_info}")
            return dict(symbol_info) if symbol_info else {}
        except (BinanceException, APIError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "get_technical_indicators":
        try:
            config = get_config()
            indicator_service = IndicatorService(client, config)
            coin_symbol = parameters.get("coin_symbol")
            if not coin_symbol:
                raise HTTPException(status_code=400, detail="Missing required parameter: coin_symbol")

            indicators = indicator_service.get_technical_indicators(coin_symbol=coin_symbol)
            logging.info(f"Returning technical indicators: {indicators}")
            return indicators or {}
        except (BinanceException, APIError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "place_order":
        required_params = ["symbol", "side", "order_type", "quantity"]
        if not all(k in parameters for k in required_params):
            raise HTTPException(status_code=400, detail=f"Missing one or more required parameters: {required_params}")
        try:
            order_service = OrderService(client)
            # This is a simplified implementation. We would need more robust parameter handling.
            order = order_service.place_order(
                symbol=parameters["symbol"],
                side=parameters["side"],
                order_type=parameters["order_type"],
                quantity=parameters["quantity"],
                price=parameters.get("price"),
                stop_price=parameters.get("stop_price"),
            )
            return dict(order) if order else {}
        except (BinanceException, APIError, ValueError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    elif action == "cancel_order":
        required_params = ["symbol", "order_type", "order_id"]
        if not all(k in parameters for k in required_params):
            raise HTTPException(status_code=400, detail=f"Missing one or more required parameters: {required_params}")
        try:
            order_service = OrderService(client)
            order = order_service.cancel_order(
                order_type=parameters["order_type"],
                symbol=parameters["symbol"],
                order_id=parameters["order_id"],
            )
            return dict(order) if order else {}
        except (BinanceException, APIError, ValueError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


def run_server() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
