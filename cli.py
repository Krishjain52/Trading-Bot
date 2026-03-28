#!/usr/bin/env python3
"""
cli.py – Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.1 --price 2500
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --price 58000
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from bot.client import BinanceAPIError, BinanceFuturesClient, NetworkError
from bot.logging_config import setup_logging
from bot.orders import place_limit_order, place_market_order, place_stop_market_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

load_dotenv()
logger = setup_logging()


# ---------------------------------------------------------------------------
# pretty printers
# ---------------------------------------------------------------------------

def _separator(char: str = "─", width: int = 56) -> None:
    print(char * width)


def _print_request_summary(args: argparse.Namespace) -> None:
    _separator()
    print("  ORDER REQUEST SUMMARY")
    _separator()
    print(f"  Symbol   : {args.symbol.upper()}")
    print(f"  Side     : {args.side.upper()}")
    print(f"  Type     : {args.type.upper()}")
    print(f"  Quantity : {args.quantity}")
    if args.price:
        print(f"  Price    : {args.price}")
    print(f"  Time     : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    _separator()
    print()


def _print_order_result(result: dict) -> None:
    _separator()
    print("  ORDER RESPONSE")
    _separator()
    for key, value in result.items():
        if value is not None:
            print(f"  {key:<14}: {value}")
    _separator()
    print()


# ---------------------------------------------------------------------------
# argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01\n"
            "  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.1 --price 2500\n"
            "  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --price 58000\n"
        ),
    )
    parser.add_argument("--symbol",   required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",     required=True, help="BUY or SELL")
    parser.add_argument("--type",     required=True, help="MARKET, LIMIT, or STOP_MARKET")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument(
        "--price",
        required=False,
        default=None,
        help="Limit / stop price (required for LIMIT and STOP_MARKET)",
    )
    parser.add_argument(
        "--tif",
        required=False,
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC)",
    )
    return parser


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── validate inputs ──────────────────────────────────────────────────
    try:
        args.symbol   = validate_symbol(args.symbol)
        args.side     = validate_side(args.side)
        args.type     = validate_order_type(args.type)
        args.quantity = validate_quantity(args.quantity)
        args.price    = validate_price(args.price, args.type)
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        print(f"\n[ERROR] {exc}\n")
        parser.print_help()
        sys.exit(1)

    _print_request_summary(args)

    # ── load credentials ─────────────────────────────────────────────────
    api_key    = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        msg = (
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set "
            "in the environment or in a .env file."
        )
        logger.error(msg)
        print(f"\n[ERROR] {msg}\n")
        sys.exit(1)

    # ── build client & place order ────────────────────────────────────────
    client = BinanceFuturesClient(api_key, api_secret)

    try:
        if args.type == "MARKET":
            result = place_market_order(client, args.symbol, args.side, args.quantity)

        elif args.type == "LIMIT":
            result = place_limit_order(
                client, args.symbol, args.side, args.quantity, args.price, args.tif
            )

        elif args.type == "STOP_MARKET":
            result = place_stop_market_order(
                client, args.symbol, args.side, args.quantity, args.price
            )

        else:
            # shouldn't reach here because the validator already caught it,
            # but just in case someone adds a new type without updating the router
            print(f"[ERROR] Unhandled order type: {args.type}")
            sys.exit(1)

    except BinanceAPIError as exc:
        logger.error("Order failed – API returned error %s: %s", exc.code, exc.message)
        print(f"\n[FAILED] Binance API error {exc.code}: {exc.message}\n")
        sys.exit(1)

    except NetworkError as exc:
        logger.error("Order failed – network issue: %s", exc)
        print(f"\n[FAILED] Network error: {exc}\n")
        sys.exit(1)

    except Exception as exc:
        logger.exception("Unexpected error while placing order")
        print(f"\n[FAILED] Unexpected error: {exc}\n")
        sys.exit(1)

    # ── print result ──────────────────────────────────────────────────────
    _print_order_result(result)
    print(f"[SUCCESS] Order submitted. ID: {result.get('orderId')}  Status: {result.get('status')}\n")


if __name__ == "__main__":
    main()
