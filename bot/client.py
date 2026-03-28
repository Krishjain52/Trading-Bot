"""
Low-level Binance Futures Testnet client.

Handles request signing, timestamp generation, and HTTP communication.
All responses are returned as raw dicts so the order layer can format them
however it wants.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Any

import requests

from bot.logging_config import setup_logging

logger = setup_logging()

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # ms – how long the server will accept a signed request


class BinanceAPIError(Exception):
    """Wraps error responses that came back from the Binance REST API."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class NetworkError(Exception):
    """Wraps low-level connectivity failures."""


class BinanceFuturesClient:
    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must be provided.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Appends a HMAC-SHA256 signature to the param dict."""
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        params = params or {}
        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = RECV_WINDOW
            params = self._sign(params)

        url = f"{BASE_URL}{endpoint}"
        logger.debug("→ %s %s  params=%s", method.upper(), url, _sanitise(params))

        try:
            resp = self._session.request(method, url, params=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error reaching %s: %s", url, exc)
            raise NetworkError(f"Could not connect to Binance Testnet: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise NetworkError(f"Request timed out: {exc}") from exc

        logger.debug("← HTTP %s  body=%s", resp.status_code, resp.text[:500])

        data = resp.json()

        if not resp.ok or (isinstance(data, dict) and "code" in data and data["code"] < 0):
            code = data.get("code", resp.status_code)
            msg = data.get("msg", resp.text)
            logger.error("API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return data

    # ------------------------------------------------------------------
    # public API wrappers
    # ------------------------------------------------------------------

    def get_server_time(self) -> dict:
        return self._request("GET", "/fapi/v1/time")

    def get_exchange_info(self, symbol: str) -> dict:
        return self._request("GET", "/fapi/v1/exchangeInfo", params={"symbol": symbol})

    def get_account(self) -> dict:
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **kwargs) -> dict:
        """
        Place a single futures order (MARKET or LIMIT) via /fapi/v1/order.
        kwargs are passed straight through as Binance API parameters.
        """
        logger.info(
            "Placing order: symbol=%s side=%s type=%s qty=%s price=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        result = self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)
        logger.info("Order placed successfully – orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def place_batch_orders(self, orders: list[dict]) -> list[dict]:
        """
        Place up to 5 orders in a single API call via /fapi/v1/batchOrders.
        Each item in orders is a dict of standard order parameters.
        """
        if not orders:
            raise ValueError("orders list cannot be empty.")
        if len(orders) > 5:
            raise ValueError("Batch orders are limited to 5 per request.")

        logger.info("Placing batch of %d orders", len(orders))
        for i, o in enumerate(orders):
            logger.debug("  batch[%d]: %s", i, o)

        params = {
            "batchOrders": json.dumps(orders),
        }
        results = self._request("POST", "/fapi/v1/batchOrders", params=params, signed=True)
        logger.info("Batch order response received – %d results", len(results))
        return results


def _sanitise(params: dict) -> dict:
    """Returns a copy of params with the signature blanked out for logging."""
    copy = dict(params)
    if "signature" in copy:
        copy["signature"] = "***"
    return copy