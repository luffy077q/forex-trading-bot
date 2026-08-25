"""
Main entry point. Runs continuously, checking each instrument on a timer,
managing open simulated positions, and opening new ones when the strategy
confirms a signal. No broker account needed -- fully self-contained paper
trading using free Yahoo Finance data.

Run with:  python main.py
Stop with: Ctrl+C
"""

import time
from datetime import datetime

import config
import indicators
import strategy
import risk_manager
import trade_logger
import market_data
import paper_broker


def run_once(state):
    # 1. Get current prices for all instruments, check open positions for SL/TP hits
    current_prices = {}
    for instrument in config.INSTRUMENTS:
        try:
            current_prices[instrument] = market_data.get_current_price(instrument)
        except Exception as e:
            print(f"{instrument}: could not fetch current price ({e}), skipping this cycle.")

    closed = paper_broker.check_and_close_positions(state, current_prices)
    for trade in closed:
        trade_logger.log_closed_trade(trade)
        print(f"{trade['instrument']}: CLOSED {trade['side']} via {trade['exit_reason']} "
              f"@ {trade['exit_price']:.5f}  P/L: {trade['pnl']:+.2f} {state['currency']}")

    balance = state["balance"]
    open_count = len(state["open_positions"])
    print(f"\n=== Check at {datetime.now().isoformat(timespec='seconds')} "
          f"| Balance: {balance:.2f} {state['currency']} "
          f"| Open positions: {open_count} ===")
    trade_logger.log_balance(balance, state["currency"], open_count)

    if open_count >= config.MAX_OPEN_POSITIONS:
        print(f"Max open positions ({config.MAX_OPEN_POSITIONS}) reached. Skipping new entries.")
        return

    # 2. Look for new signals
    for instrument in config.INSTRUMENTS:
        try:
            if paper_broker.has_open_position(state, instrument):
                print(f"{instrument}: already have an open position, skipping.")
                continue

            candles = market_data.get_candles(instrument)
            df = indicators.compute_all(
                candles, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD
            )

            evaluation = strategy.evaluate(instrument, df)
            trade_logger.log_signal(evaluation)

            decision = evaluation["final_decision"]
            print(f"{instrument}: technical={evaluation['technical_signal']} "
                  f"news_net={evaluation['news_net']} -> {decision or 'NO TRADE'} "
                  f"({evaluation['reason']})")

            if decision is None:
                continue

            entry_price = current_prices.get(instrument) or evaluation["close"]
            atr = evaluation["atr"]
            stop_loss, take_profit, sl_distance = risk_manager.calculate_stops(
                instrument, decision, entry_price, atr
            )
            units = risk_manager.calculate_position_size(state["balance"], sl_distance, instrument)

            if units <= 0:
                print(f"{instrument}: calculated position size is 0, skipping.")
                continue

            position = paper_broker.open_position(
                state, instrument, decision, units, entry_price, stop_loss, take_profit
            )
            trade_logger.log_trade(instrument, decision, units, entry_price, stop_loss, take_profit, None)
            print(f"{instrument}: OPENED {decision} {units} units @ ~{entry_price:.5f} "
                  f"SL={stop_loss:.5f} TP={take_profit:.5f}")

        except Exception as e:
            print(f"{instrument}: ERROR - {e}")


def main():
    state = paper_broker.load_state()
    print(f"Starting paper trading bot. Starting balance: {state['balance']:.2f} {state['currency']}")
    print(f"Checking every {config.CHECK_INTERVAL_MINUTES} minutes. Press Ctrl+C to stop.")
    print(f"Account state is saved in {config.PAPER_STATE_FILE} -- delete that file to reset your virtual balance.\n")

    while True:
        try:
            state = paper_broker.load_state()  # reload in case dashboard or another process touched it
            run_once(state)
        except Exception as e:
            print(f"Top-level error (bot will keep running): {e}")
        time.sleep(config.CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
