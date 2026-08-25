"""
Position sizing and stop-loss/take-profit calculation.
Never risks more than config.RISK_PER_TRADE_PCT of account equity on a trade.
"""

import config


def pip_size(instrument):
    # JPY pairs have pip = 0.01, others 0.0001
    return 0.01 if instrument.endswith("JPY") else 0.0001


def calculate_stops(instrument, side, entry_price, atr):
    pip = pip_size(instrument)
    sl_distance = atr * config.STOP_LOSS_ATR_MULTIPLE
    tp_distance = atr * config.TAKE_PROFIT_ATR_MULTIPLE

    if side == "BUY":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    else:
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance

    return stop_loss, take_profit, sl_distance


def calculate_position_size(account_balance, sl_distance_price, instrument, quote_to_account_rate=1.0):
    """
    Simple position sizing: risk a fixed % of balance, size = risk_amount / stop_distance.
    quote_to_account_rate lets you convert if account currency != quote currency
    (default 1.0 assumes account currency == quote currency, true for USD accounts
    trading pairs quoted in USD; adjust if needed).
    Returns units (int), rounded down, always >= 0.
    """
    risk_amount = account_balance * (config.RISK_PER_TRADE_PCT / 100.0)
    if sl_distance_price <= 0:
        return 0
    units = risk_amount / (sl_distance_price * quote_to_account_rate)
    return int(units)
