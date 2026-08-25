"""
Free, no-signup market data via Yahoo Finance (through the yfinance library).
Replaces the need for a broker account just to get price data for paper trading.

Note: Yahoo Finance is a free, unofficial data source. It's reliable enough
for paper trading and strategy testing, but occasionally has brief outages
or rate limits. It is NOT something to rely on for real-money execution --
when you go live with a real broker, that broker's own price feed is used
for actual order fills.
"""

import pandas as pd
import yfinance as yf
import config


def get_candles(instrument_code, interval=None, period=None):
    """
    instrument_code: internal code like 'EUR_USD' (looked up in config.INSTRUMENTS)
    Returns a list of dicts: time, open, high, low, close -- same shape the
    rest of the bot (indicators.py, strategy.py) already expects.
    """
    ticker = config.INSTRUMENTS[instrument_code]
    interval = interval or config.CANDLE_INTERVAL
    period = period or config.CANDLE_PERIOD

    df = yf.Ticker(ticker).history(interval=interval, period=period)
    if df.empty:
        raise RuntimeError(f"No data returned for {ticker} ({instrument_code}). "
                            f"Check your internet connection or try again shortly.")

    df = df.reset_index()
    time_col = "Datetime" if "Datetime" in df.columns else "Date"

    candles = []
    for _, row in df.iterrows():
        candles.append({
            "time": row[time_col].isoformat(),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
        })
    return candles


def get_current_price(instrument_code):
    """Returns the latest available price (last close of the most recent candle)."""
    ticker = config.INSTRUMENTS[instrument_code]
    df = yf.Ticker(ticker).history(interval="1m", period="1d")
    if df.empty:
        # Fall back to hourly if 1-minute data isn't available (e.g. market closed)
        df = yf.Ticker(ticker).history(interval="1h", period="5d")
    if df.empty:
        raise RuntimeError(f"Could not fetch current price for {ticker} ({instrument_code}).")
    return float(df["Close"].iloc[-1])
