# Binance Futures Testnet Trading Bot

A lightweight Python CLI tool for placing orders on the Binance Futures Testnet (USDT-M). Built with clean separation between the API client, order logic, and CLI layer.

---

## Features

- Place **MARKET** and **LIMIT** orders on any USDT-M futures pair
- **BATCH** order support (bonus) – ladder into a position across multiple price levels in a single API call
- Supports both **BUY** and **SELL** sides
- Input validation before any API call is made
- Structured logging to a rotating log file (DEBUG level) and stdout (INFO level)
- Graceful error handling for API errors, network failures, and bad input
- Credentials loaded from a `.env` file – no hardcoding

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, HTTP, error handling)
│   ├── orders.py          # Order placement functions (market, limit, batch)
│   ├── validators.py      # Input validation – runs before any API call
│   └── logging_config.py  # Rotating file + console logging setup
├── logs/
│   ├── market_order.log   # Sample market order log
│   └── limit_order.log    # Sample limit order log
├── cli.py                 # CLI entry point (argparse)
├── .env.example           # Template for API credentials
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet API credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Register with your email address
3. Log in, then scroll to the bottom of the page and click **API Key**
4. Click **Generate** – copy your API Key and Secret immediately (the secret is only shown once)

### 2. Clone the repo

```bash
git clone https://github.com/Krishjain52/Trading-Bot.git
cd Trading-Bot
```

### 3. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure credentials

```bash
cp .env.example .env
# Open .env and paste in your testnet API key and secret
```

Your `.env` should look like:

```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

---

## How to Run

### MARKET order

```bash
python3 cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### LIMIT order

```bash
python3 cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 2500
```

With a custom time-in-force (default is GTC):

```bash
python3 cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 60000 --tif IOC
```

### BATCH order (bonus)

Place multiple LIMIT orders at different price levels in a single API call.
Useful for laddering into a position without making multiple round trips to the exchange.

```bash
python3 cli.py --symbol BTCUSDT --side BUY --type BATCH --quantity 0.01 --prices 60000,61000,62000
```

Up to 5 price levels supported per batch.

### Help

```bash
python3 cli.py --help
```

---

## Sample Output

```
────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Symbol   : BTCUSDT
  Side     : BUY
  Type     : MARKET
  Quantity : 0.01
  Time     : 2026-03-28 14:22:03 UTC
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
  ORDER RESPONSE
────────────────────────────────────────────────────────
  orderId       : 13002236695
  symbol        : BTCUSDT
  side          : BUY
  type          : MARKET
  origQty       : 0.010
  executedQty   : 0.010
  avgPrice      : 84312.50000
  status        : FILLED
  timeInForce   : GTC
  updateTime    : 1774705425994
────────────────────────────────────────────────────────

[SUCCESS] Order submitted. ID: 13002236695  Status: FILLED
```

---

## CLI Reference

| Flag | Required | Description |
|---|---|---|
| `--symbol` | Yes | Trading pair, e.g. `BTCUSDT` |
| `--side` | Yes | `BUY` or `SELL` |
| `--type` | Yes | `MARKET`, `LIMIT`, or `BATCH` |
| `--quantity` | Yes | Order quantity per order |
| `--price` | LIMIT only | Limit price |
| `--prices` | BATCH only | Comma-separated prices, e.g. `60000,61000,62000` |
| `--tif` | No | Time-in-force: `GTC` (default), `IOC`, `FOK` |

---

## Logging

Logs are written to `logs/trading_bot.log` automatically. The file rotates at 5 MB and keeps up to 5 backups.

- **DEBUG** – full request/response detail (params, HTTP status, raw body)
- **INFO** – order placement events and outcomes
- **ERROR** – validation failures, API errors, network issues

---

## Error Handling

| Situation | What happens |
|---|---|
| Missing required argument | `argparse` prints help and exits |
| Invalid symbol / side / type | `ValidationError` with a clear message before any HTTP call |
| Price missing for LIMIT order | `ValidationError` – caught before hitting the API |
| More than 5 prices in BATCH | `ValidationError` with explanation |
| Binance returns an error code | `BinanceAPIError` printed with code + message |
| No internet / DNS failure | `NetworkError` with connection details |
| Unexpected exception | Logged with full traceback, clean exit message |

---

## Assumptions

- **Testnet only** – the base URL is hardcoded to `https://testnet.binancefuture.com`. Switching to production only requires changing `BASE_URL` in `bot/client.py`.
- **Quantity precision** – quantities are passed as-is. If the exchange rejects a precision error, the API error message will indicate the correct step size for that symbol.
- **BATCH orders** use LIMIT type internally and are limited to 5 orders per request by the Binance API.
- **Conditional order types** (STOP_MARKET, TAKE_PROFIT_MARKET) are not supported on this testnet endpoint and are therefore not included.
- Python 3.9+ required.

---

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for Binance REST API |
| `python-dotenv` | Loads `.env` credentials into the environment |