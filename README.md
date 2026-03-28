# Binance Futures Testnet Trading Bot

A lightweight Python CLI tool for placing orders on the Binance Futures Testnet (USDT-M). Built with clean separation between the API client, order logic, and CLI layer.

---

## Features

- Place **MARKET**, **LIMIT**, and **STOP_MARKET** orders
- Supports **BUY** and **SELL** on any USDT-M futures pair
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
│   ├── orders.py          # Order placement functions (market, limit, stop)
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
2. Log in with your GitHub account
3. Click **API Key** in the top-right menu
4. Copy your API key and secret

### 2. Clone / download the repo

```bash
git clone <your-repo-url>
cd trading_bot
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv
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
# Open .env in your editor and paste in your testnet API key and secret
```

Your `.env` should look like:

```
BINANCE_API_KEY=abc123...
BINANCE_API_SECRET=xyz789...
```

---

## How to Run

### MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### LIMIT order

```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 2500
```

With a custom time-in-force (default is GTC):

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 60000 --tif IOC
```

### STOP_MARKET order (bonus order type)

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --price 58000
```

### Help

```bash
python cli.py --help
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
  Time     : 2025-06-10 14:22:03 UTC
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
  ORDER RESPONSE
────────────────────────────────────────────────────────
  orderId       : 4100347291
  symbol        : BTCUSDT
  side          : BUY
  type          : MARKET
  origQty       : 0.01
  executedQty   : 0.01
  avgPrice      : 67412.30000
  status        : FILLED
  timeInForce   : GTC
  updateTime    : 1749562923430
────────────────────────────────────────────────────────

[SUCCESS] Order submitted. ID: 4100347291  Status: FILLED
```

---

## Logging

Logs are written to `logs/trading_bot.log` automatically. The file rotates once it hits 5 MB and keeps up to 5 backups.

- **DEBUG** – full request/response detail (params, HTTP status, raw body)
- **INFO** – order placement events and outcomes
- **ERROR** – validation failures, API errors, network issues

Sample log entries are included in the `logs/` directory.

---

## Error Handling

| Situation | What happens |
|---|---|
| Missing required arg | `argparse` prints help and exits |
| Invalid symbol / side / type | `ValidationError` with a clear message |
| Price missing for LIMIT order | `ValidationError` before any HTTP call |
| Binance returns an error code | `BinanceAPIError` printed with code + message |
| No internet / DNS failure | `NetworkError` with connection details |
| Unexpected exception | Logged with full traceback, clean exit message |

---

## Assumptions

- Testnet only – the base URL is hardcoded to `https://testnet.binancefuture.com`. Swapping to production would just mean changing `BASE_URL` in `client.py`.
- Quantities are passed as-is to the API. If the exchange rejects a quantity precision error, the API error message will tell you the correct step size for that symbol.
- STOP_MARKET orders use `closePosition=false` – they open/add to a position rather than closing one.
- Python 3.9+ is assumed (uses `dict | None` union syntax).

---

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for Binance REST API |
| `python-dotenv` | Loads `.env` credentials into the environment |
