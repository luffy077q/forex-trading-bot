# Forex Paper Trading Bot

A trend-following forex bot for **EUR/USD, GBP/USD, USD/JPY** that combines
technical signals (EMA crossover + RSI) with a news-sentiment filter, paper
trades using free real-time market data, and shows everything on a local
website. **No broker account or signup required to get started.**

⚠️ **Read this before running anything:**
- This is a **rules-based strategy bot**, not a guaranteed-profit system. No such thing exists.
- Paper trade for weeks, across different market conditions, before ever thinking about real money.
- Real trading — anywhere, with any bot — carries genuine risk of loss.

## Why this doesn't use OANDA or Zerodha

- **OANDA isn't available to Indian residents.** RBI's FEMA rules only allow Indian residents to trade forex through SEBI-registered brokers on Indian exchanges (NSE/BSE), in specific approved pairs — not through offshore retail brokers like OANDA.
- **Zerodha doesn't offer EUR/USD, GBP/USD, or USD/JPY at all.** These "cross-currency" pairs exist on NSE but only a few brokers (e.g. Sharekhan) list them, and RBI requires proof of an underlying currency exposure to trade them.
- So for paper trading, this bot sidesteps brokers entirely: it pulls free, real market prices from Yahoo Finance and simulates trades locally in a file on your computer. Zero setup, zero legal complications, completely free. See "Going live" below for the real-money picture once you're ready.

## 1. Setup

```bash
pip install -r requirements.txt
```
That's it — no accounts, no API keys needed to start paper trading. (A NewsAPI key is optional, see below.)

### (Optional) Get a free NewsAPI key for the news-sentiment filter
1. Sign up at https://newsapi.org (free tier: 100 requests/day)
2. Copy your API key into `config.py`, or set it as an environment variable:
```bash
export NEWSAPI_KEY="your-newsapi-key"
```
If you skip this, the bot runs on technical signals only — it just won't filter trades against news sentiment.

## 2. Backtest first

Before running anything live, test the strategy against ~2 years of historical data:
```bash
python backtest.py            # tests all configured pairs
python backtest.py EUR_USD    # tests one pair
```
This shows win rate and total P/L in price terms. **It ignores spread and slippage**, so real results will be somewhat worse — use it only to sanity-check that there's *some* edge before paper trading. If a pair shows a poor win rate/P/L, consider adjusting the EMA periods in `config.py`.

## 3. Paper trade

```bash
python main.py
```
This runs continuously (leave the terminal open), checking every 15 minutes by default. It will:
- Pull the latest price data from Yahoo Finance (free, no key needed)
- Check for an EMA crossover + RSI signal
- Check news sentiment as a filter (skipped automatically if no NewsAPI key)
- Log every check to `signal_log.csv` — even when no trade is made, so you can see *why*
- Open a simulated position with automatic stop-loss/take-profit when a signal is confirmed
- Check open positions every cycle and close them when price hits the stop-loss or take-profit
- Track your virtual balance in `paper_account.json` (starts at $10,000 — change `STARTING_BALANCE` in `config.py` if you want)

Stop anytime with `Ctrl+C`. To reset your virtual account, just delete `paper_account.json`.

## 4. Watch it on the dashboard website

In a **second terminal** (leave `main.py` running in the first one):
```bash
python dashboard.py
```
Then open **http://localhost:5000** in your browser. You'll see:
- Live virtual balance and open positions
- A balance-over-time chart
- Closed trades with realized profit/loss
- Every signal check the bot has made — including trades it *skipped* and exactly why (technical values, news sentiment scores, reasoning)

The page auto-refreshes every 30 seconds. It's read-only — it only displays what `main.py` is doing. It runs only on your own computer (`localhost`), so nobody else can see it.

## 5. Going live (real money) — the honest picture for India

This is genuinely more complicated than in the US, and worth understanding before you commit:
- Your exact pairs (EUR/USD, GBP/USD, USD/JPY) are only offered as NSE derivative contracts by a handful of brokers (Sharekhan is the most commonly cited), and RBI requires you to declare an underlying currency exposure to trade them.
- The much simpler legal path is trading **INR pairs** (USD/INR, EUR/INR, GBP/INR, JPY/INR) via a SEBI-registered broker like Zerodha (Kite Connect API), which is well-documented and doesn't require the exposure declaration for INR pairs.
- Either way, going live means: a funded brokerage account, KYC, and (for Zerodha) a paid Kite Connect API subscription.

**My suggestion**: run this paper trading setup for a while first. Once you have real performance data and want to go live, tell me which route you'd rather take (cross-currency via a broker like Sharekhan, or switch the bot to trade INR pairs via Zerodha) and I'll adapt the code — the strategy, risk management, and dashboard all carry over either way; only the execution layer changes.

## Files
| File | Purpose |
|---|---|
| `config.py` | All settings — pairs, risk %, indicator periods, virtual starting balance |
| `market_data.py` | Free price data via Yahoo Finance |
| `paper_broker.py` | Fully simulated trading account (balance, positions, P/L) — no broker needed |
| `indicators.py` | EMA, RSI, ATR calculations |
| `news_sentiment.py` | Keyword-based news sentiment scoring |
| `strategy.py` | Combines technical + news into a final decision |
| `risk_manager.py` | Position sizing and stop-loss/take-profit calculation |
| `trade_logger.py` | Writes `signal_log.csv`, `trade_log.csv`, `closed_trades.csv`, `balance_log.csv` |
| `main.py` | The paper trading loop |
| `dashboard.py` | Local website (http://localhost:5000) showing everything the bot does |
| `backtest.py` | Historical backtest of the technical strategy |

## Tuning ideas once you have data
- Adjust `EMA_FAST`/`EMA_SLOW` in `config.py` — shorter periods trade more often but with more noise
- Adjust `RISK_PER_TRADE_PCT` — start conservative (0.5–1%)
- Widen/narrow `NEWS_BLOCK_THRESHOLD` depending on how much you trust the sentiment filter
- Add more instruments to `INSTRUMENTS` in `config.py` (any pair with a Yahoo Finance ticker works, e.g. `AUD_USD: "AUDUSD=X"`)
