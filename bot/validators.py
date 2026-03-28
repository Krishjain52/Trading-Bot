"""
Input validation for CLI args before they reach the API layer.
Keeping this separate means the client stays clean and we can
unit-test validation independently.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s:
        raise ValidationError("Symbol cannot be empty.")
    if not s.isalnum():
        raise ValidationError(f"Symbol '{s}' contains invalid characters. Example: BTCUSDT")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Side must be one of {VALID_SIDES}, got '{side}'.")
    return s


def validate_order_type(order_type: str) -> str:
    ot = order_type.strip().upper()
    if ot not in VALID_ORDER_TYPES:
        raise ValidationError(f"Order type must be one of {VALID_ORDER_TYPES}, got '{order_type}'.")
    return ot


def validate_quantity(qty: str) -> float:
    try:
        value = float(qty)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{qty}'.")
    if value <= 0:
        raise ValidationError(f"Quantity must be positive, got {value}.")
    return value


def validate_price(price: str | None, order_type: str) -> float | None:
    """
    Price is required for LIMIT orders, must not be supplied for MARKET orders.
    For STOP_MARKET we still allow an optional stopPrice to be passed separately,
    so this function just handles the main price field.
    """
    if order_type == "MARKET":
        if price is not None:
            raise ValidationError("Price should not be provided for MARKET orders.")
        return None

    if order_type in ("LIMIT", "STOP_MARKET"):
        if price is None:
            raise ValidationError(f"Price is required for {order_type} orders.")
        try:
            value = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a number, got '{price}'.")
        if value <= 0:
            raise ValidationError(f"Price must be positive, got {value}.")
        return value

    return None
