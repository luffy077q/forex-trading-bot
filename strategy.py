"""
Combines technical signals with the news sentiment filter to produce a final
trade decision. This is the module to edit if you want to change the
strategy logic itself.
"""

import config
import indicators
import news_sentiment


def technical_signal(df):
    """
    Returns 'BUY', 'SELL', or None based on the latest completed candle.
    Logic: EMA fast/slow crossover confirmed by RSI not being at an extreme.
    """
    if len(df) < max(config.EMA_SLOW, config.RSI_PERIOD) + 2:
        return None, {}

    prev = df.iloc[-2]
    last = df.iloc[-1]

    crossed_up = prev["ema_fast"] <= prev["ema_slow"] and last["ema_fast"] > last["ema_slow"]
    crossed_down = prev["ema_fast"] >= prev["ema_slow"] and last["ema_fast"] < last["ema_slow"]

    details = {
        "ema_fast": last["ema_fast"],
        "ema_slow": last["ema_slow"],
        "rsi": last["rsi"],
        "atr": last["atr"],
        "close": last["close"],
    }

    if crossed_up and last["rsi"] < config.RSI_OVERBOUGHT:
        return "BUY", details
    if crossed_down and last["rsi"] > config.RSI_OVERSOLD:
        return "SELL", details

    return None, details


def evaluate(instrument, df):
    """
    Full decision pipeline for one instrument.
    Returns a dict describing the decision and the reasoning (for logging).
    """
    signal, details = technical_signal(df)

    result = {
        "instrument": instrument,
        "technical_signal": signal,
        **details,
        "news_base": None,
        "news_quote": None,
        "news_net": None,
        "final_decision": None,
        "reason": None,
    }

    if signal is None:
        result["reason"] = "no technical signal"
        return result

    base_score, quote_score, net_score = news_sentiment.get_pair_sentiment(instrument)
    result["news_base"] = base_score
    result["news_quote"] = quote_score
    result["news_net"] = net_score

    # Block the trade if news strongly contradicts the technical signal
    if signal == "BUY" and net_score < -config.NEWS_BLOCK_THRESHOLD:
        result["reason"] = f"BUY signal blocked: news net score {net_score:.2f} is bearish"
        return result
    if signal == "SELL" and net_score > config.NEWS_BLOCK_THRESHOLD:
        result["reason"] = f"SELL signal blocked: news net score {net_score:.2f} is bullish"
        return result

    result["final_decision"] = signal
    result["reason"] = "technical signal confirmed (news neutral or supportive)"
    return result
