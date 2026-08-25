"""
Technical indicators computed with plain Python/pandas -- no exotic dependencies.
"""

import pandas as pd


def candles_to_df(candles):
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def add_ema(df, period, col="close", out_col=None):
    out_col = out_col or f"ema_{period}"
    df[out_col] = df[col].ewm(span=period, adjust=False).mean()
    return df


def add_rsi(df, period=14, col="close", out_col="rsi"):
    delta = df[col].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    df[out_col] = 100 - (100 / (1 + rs))
    return df


def add_atr(df, period=14, out_col="atr"):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df[out_col] = tr.ewm(alpha=1 / period, adjust=False).mean()
    return df


def compute_all(candles, ema_fast, ema_slow, rsi_period, atr_period):
    df = candles_to_df(candles)
    add_ema(df, ema_fast, out_col="ema_fast")
    add_ema(df, ema_slow, out_col="ema_slow")
    add_rsi(df, rsi_period)
    add_atr(df, atr_period)
    return df
