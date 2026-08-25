"""
Backtests the technical strategy (EMA crossover + RSI) against historical
data pulled free from Yahoo Finance. News sentiment is NOT included here
since free news APIs don't provide historical headlines for arbitrary past
dates -- this tests the technical edge in isolation, which is a reasonable
first filter: if the technical strategy alone isn't profitable, adding a
news filter won't save it.

Run with: python backtest.py EUR_USD
(or with no argument to test all configured instruments)
"""

import sys
import config
import indicators
import market_data


def backtest_instrument(instrument, period="730d"):
    candles = market_data.get_candles(instrument, interval=config.CANDLE_INTERVAL, period=period)
    df = indicators.compute_all(
        candles, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD
    )

    trades = []
    position = None  # dict with side, entry, sl, tp

    for i in range(max(config.EMA_SLOW, config.RSI_PERIOD) + 2, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]

        # Manage open position first
        if position:
            hit_sl = (position["side"] == "BUY" and row["low"] <= position["sl"]) or \
                     (position["side"] == "SELL" and row["high"] >= position["sl"])
            hit_tp = (position["side"] == "BUY" and row["high"] >= position["tp"]) or \
                     (position["side"] == "SELL" and row["low"] <= position["tp"])

            if hit_sl or hit_tp:
                exit_price = position["sl"] if hit_sl else position["tp"]
                pnl_price = (exit_price - position["entry"]) if position["side"] == "BUY" else (position["entry"] - exit_price)
                trades.append(pnl_price)
                position = None

        if position:
            continue  # only one position at a time in this simple backtest

        crossed_up = prev["ema_fast"] <= prev["ema_slow"] and row["ema_fast"] > row["ema_slow"]
        crossed_down = prev["ema_fast"] >= prev["ema_slow"] and row["ema_fast"] < row["ema_slow"]

        if crossed_up and row["rsi"] < config.RSI_OVERBOUGHT:
            sl = row["close"] - row["atr"] * config.STOP_LOSS_ATR_MULTIPLE
            tp = row["close"] + row["atr"] * config.TAKE_PROFIT_ATR_MULTIPLE
            position = {"side": "BUY", "entry": row["close"], "sl": sl, "tp": tp}
        elif crossed_down and row["rsi"] > config.RSI_OVERSOLD:
            sl = row["close"] + row["atr"] * config.STOP_LOSS_ATR_MULTIPLE
            tp = row["close"] - row["atr"] * config.TAKE_PROFIT_ATR_MULTIPLE
            position = {"side": "SELL", "entry": row["close"], "sl": sl, "tp": tp}

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    total = sum(trades)
    win_rate = (len(wins) / len(trades) * 100) if trades else 0

    print(f"\n--- {instrument} backtest ({len(df)} candles, {config.CANDLE_INTERVAL}) ---")
    print(f"Total trades: {len(trades)}")
    print(f"Win rate: {win_rate:.1f}%  ({len(wins)} wins / {len(losses)} losses)")
    print(f"Total P/L (price units, not accounting for spread/slippage): {total:.5f}")
    if trades:
        print(f"Avg win: {sum(wins)/len(wins):.5f}" if wins else "Avg win: n/a")
        print(f"Avg loss: {sum(losses)/len(losses):.5f}" if losses else "Avg loss: n/a")

    return trades


def main():
    instruments = [sys.argv[1]] if len(sys.argv) > 1 else list(config.INSTRUMENTS.keys())

    for instrument in instruments:
        try:
            backtest_instrument(instrument)
        except Exception as e:
            print(f"{instrument}: backtest failed - {e}")

    print("\nNOTE: This backtest ignores spread, slippage, and news filtering -- "
          "real results will be worse than shown here. Use this only to sanity-check "
          "whether the technical logic has any edge before paper trading.")


if __name__ == "__main__":
    main()
