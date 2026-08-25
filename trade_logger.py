"""
Simple CSV-based logging so you can review every decision the bot made,
not just the trades it executed. Open these files in Excel/Sheets anytime.
"""

import csv
import os
from datetime import datetime, timezone
import config


def _write_row(filepath, fieldnames, row):
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def log_signal(evaluation: dict):
    fieldnames = [
        "timestamp", "instrument", "technical_signal", "close", "ema_fast",
        "ema_slow", "rsi", "atr", "news_base", "news_quote", "news_net",
        "final_decision", "reason",
    ]
    row = {"timestamp": datetime.now(timezone.utc).isoformat()}
    row.update({k: evaluation.get(k) for k in fieldnames if k != "timestamp"})
    _write_row(config.SIGNAL_LOG_FILE, fieldnames, row)


def log_trade(instrument, side, units, entry_price, stop_loss, take_profit, order_response):
    fieldnames = [
        "timestamp", "instrument", "side", "units", "entry_price",
        "stop_loss", "take_profit", "order_id",
    ]
    order_id = None
    if isinstance(order_response, dict):
        fill = order_response.get("orderFillTransaction", {})
        order_id = fill.get("id") or order_response.get("orderCreateTransaction", {}).get("id")

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instrument": instrument,
        "side": side,
        "units": units,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "order_id": order_id,
    }
    _write_row(config.TRADE_LOG_FILE, fieldnames, row)


def log_balance(balance, currency, open_trade_count):
    fieldnames = ["timestamp", "balance", "currency", "open_trade_count"]
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "balance": balance,
        "currency": currency,
        "open_trade_count": open_trade_count,
    }
    _write_row(config.BALANCE_LOG_FILE, fieldnames, row)


def log_closed_trade(closed_trade: dict):
    fieldnames = [
        "closed_at", "instrument", "side", "units", "entry_price",
        "exit_price", "exit_reason", "pnl", "opened_at",
    ]
    row = {k: closed_trade.get(k) for k in fieldnames}
    _write_row("closed_trades.csv", fieldnames, row)
