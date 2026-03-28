"""
Order placement logic – sits between the CLI and the raw API client.

Each function builds the right parameter dict, calls the client, and
returns a normalised summary dict that the CLI can print without knowing
anything about raw Binance response shapes.
"""

from __future__ import annotations

from typing import Any

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logging

logger = setup_logging()


def _normalise_response(raw: dict) -> dict:
    """
    Pull out the fields we actually care about showing to the user
    so the CLI doesn't have to dig into the raw response.
    """
    return {
        "orderId": raw.get("orderId"),
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "type": raw.get("type"),
        "origQty": raw.get("origQty"),
        "executedQty": raw.get("executedQty"),
        "avgPrice": raw.get("avgPrice") or raw.get("price") or "N/A",
        "status": raw.get("status"),
        "timeInForce": raw.get("timeInForce", "N/A"),
        "updateTime": raw.get("updateTime"),
    }


def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
) -> dict[str, Any]:
    logger.debug("Building MARKET order params symbol=%s side=%s qty=%s", symbol, side, quantity)
    raw = client.place_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )
    return _normalise_response(raw)


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> dict[str, Any]:
    logger.debug(
        "Building LIMIT order params symbol=%s side=%s qty=%s price=%s tif=%s",
        symbol, side, quantity, price, time_in_force,
    )
    raw = client.place_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=price,
        timeInForce=time_in_force,
    )
    return _normalise_response(raw)


def place_batch_limit_orders(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    prices: list[float],
    time_in_force: str = "GTC",
) -> list[dict[str, Any]]:
    """
    Bonus order type – place multiple LIMIT orders at different price levels
    in a single API call using /fapi/v1/batchOrders.

    Useful for laddering into a position across several price levels without
    making multiple round trips to the exchange.
    """
    orders = [
        {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": str(quantity),
            "price": str(price),
            "timeInForce": time_in_force,
        }
        for price in prices
    ]
    logger.debug("Submitting %d batch LIMIT orders at prices %s", len(orders), prices)
    results = client.place_batch_orders(orders)
    return [_normalise_response(r) for r in results]