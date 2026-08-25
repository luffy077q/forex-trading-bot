"""
Central configuration for the forex bot.
Edit the values below before running.

This version paper-trades using free public market data (Yahoo Finance) --
no broker account needed. OANDA isn't available to Indian residents, and
Zerodha doesn't list EUR/USD, GBP/USD, or USD/JPY (only Sharekhan and a
few others do, and RBI requires proof of underlying currency exposure to
trade them). See README.md for the plan on going live later.
"""

import os

# ---------------------------------------------------------------------------
# Instruments. Internal code -> Yahoo Finance ticker.
# ---------------------------------------------------------------------------
INSTRUMENTS = {
    "EUR_USD": "EURUSD=X",
    "GBP_USD": "GBPUSD=X",
    "USD_JPY": "USDJPY=X",
}

# ---------------------------------------------------------------------------
# News sentiment (optional but recommended)
# Free tier at https://newsapi.org (100 requests/day free)
# Leave blank to run technical-only (news filter will be skipped automatically).
# ---------------------------------------------------------------------------
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")

# ---------------------------------------------------------------------------
# Paper trading account (fully simulated, no broker)
# ---------------------------------------------------------------------------
STARTING_BALANCE = 10000.0       # virtual balance, in the currency below
ACCOUNT_CURRENCY = "USD"
PAPER_STATE_FILE = "paper_account.json"

# ---------------------------------------------------------------------------
# Trading parameters
# ---------------------------------------------------------------------------
CANDLE_INTERVAL = "1h"           # hourly candles (yfinance format)
CANDLE_PERIOD = "60d"            # how much history to pull each check (max ~730d for 1h bars)

CHECK_INTERVAL_MINUTES = 15      # how often the bot checks for new signals

# Indicator settings
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ATR_PERIOD = 14

# Risk management
RISK_PER_TRADE_PCT = 1.0         # % of account balance risked per trade
STOP_LOSS_ATR_MULTIPLE = 1.5
TAKE_PROFIT_ATR_MULTIPLE = 2.5
MAX_OPEN_POSITIONS = 3           # across all instruments combined

# News filter sensitivity: minimum |sentiment score| to actively block a trade
NEWS_BLOCK_THRESHOLD = 0.4

# Logging
TRADE_LOG_FILE = "trade_log.csv"
SIGNAL_LOG_FILE = "signal_log.csv"
BALANCE_LOG_FILE = "balance_log.csv"

# Dashboard website settings
DASHBOARD_PORT = 5000
DASHBOARD_REFRESH_SECONDS = 30

