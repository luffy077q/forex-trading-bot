"""
A completely self-contained paper trading account. No broker, no API keys,
no signup -- just tracks a virtual balance and open positions in a local
JSON file (paper_account.json). Real market prices (from market_data.py)
are used to open/close simulated positions, so results are realistic, but
no real money or real orders are ever involved.

This means: works from anywhere, including India, with zero legal
complications, and zero setup beyond running the script.
"""

import json
import os
from datetime import datetime, timezone
import config


def _default_state():
    return {
        "balance": config.STARTING_BALANCE,
        "currency": config.ACCOUNT_CURRENCY,
        "open_positions": [],   # list of dicts: instrument, side, units, entry_price, stop_loss, take_profit, opened_at
        "closed_trades": [],    # history, appended on close
    }


def load_state():
    if not os.path.isfile(config.PAPER_STATE_FILE):
        state = _default_state()
        save_state(state)
        return state
    with open(config.PAPER_STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(config.PAPER_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def has_open_position(state, instrument):
    return any(p["instrument"] == instrument for p in state["open_positions"])


def open_position(state, instrument, side, units, entry_price, stop_loss, take_profit):
    position = {
        "instrument": instrument,
        "side": side,               # "BUY" or "SELL"
        "units": units,              # always positive; side determines direction
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }
    state["open_positions"].append(position)
    save_state(state)
    return position


def _pnl(position, exit_price):
    """P/L in account currency, using the same simplified units convention as risk_manager."""
    if position["side"] == "BUY":
        return (exit_price - position["entry_price"]) * position["units"]
    else:
        return (position["entry_price"] - exit_price) * position["units"]


def check_and_close_positions(state, current_prices):
    """
    current_prices: dict instrument -> latest price
    Closes any position whose stop-loss or take-profit has been hit.
    Returns list of closed trade dicts (for logging).
    """
    still_open = []
    closed = []

    for position in state["open_positions"]:
        price = current_prices.get(position["instrument"])
        if price is None:
            still_open.append(position)
            continue

        hit_sl = (position["side"] == "BUY" and price <= position["stop_loss"]) or \
                 (position["side"] == "SELL" and price >= position["stop_loss"])
        hit_tp = (position["side"] == "BUY" and price >= position["take_profit"]) or \
                 (position["side"] == "SELL" and price <= position["take_profit"])

        if hit_sl or hit_tp:
            exit_price = position["stop_loss"] if hit_sl else position["take_profit"]
            pnl = _pnl(position, exit_price)
            state["balance"] += pnl

            closed_trade = {
                **position,
                "exit_price": exit_price,
                "exit_reason": "stop_loss" if hit_sl else "take_profit",
                "pnl": pnl,
                "closed_at": datetime.now(timezone.utc).isoformat(),
            }
            state["closed_trades"].append(closed_trade)
            closed.append(closed_trade)
        else:
            still_open.append(position)

    state["open_positions"] = still_open
    save_state(state)
    return closed
