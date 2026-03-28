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
        "stopPrice": raw.get("stopPrice"),
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


def place_stop_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    stop_price: float,
) -> dict[str, Any]:
    """
    Bonus order type – STOP_MARKET triggers a market order once
    the mark price crosses stop_price.

    For a SELL stop: stopPrice must be below current market price.
    For a BUY stop:  stopPrice must be above current market price.
    """
    logger.debug(
        "Building STOP_MARKET order params symbol=%s side=%s qty=%s stopPrice=%s",
        symbol, side, quantity, stop_price,
    )
    raw = client.place_order(
        symbol=symbol,
        side=side,
        type="STOP_MARKET",
        quantity=quantity,
        stopPrice=stop_price,
        workingType="MARK_PRICE",
    )
    return _normalise_response(raw)