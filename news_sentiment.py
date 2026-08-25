"""
Lightweight news sentiment filter.

Pulls recent headlines for a currency (via NewsAPI) and scores them with a
keyword-based approach. This is intentionally simple and transparent rather
than a black-box ML model -- you can see exactly why a trade was blocked or
allowed by checking signal_log.csv.

If NEWSAPI_KEY is not set in config.py, this module always returns a neutral
score (0.0) and the bot runs technical-only.
"""

import requests
import config

CURRENCY_KEYWORDS = {
    "EUR": ["euro", "eurozone", "ecb", "european central bank"],
    "USD": ["dollar", "federal reserve", "fed ", "fomc", "us economy"],
    "GBP": ["pound", "sterling", "bank of england", "boe "],
    "JPY": ["yen", "bank of japan", "boj "],
}

POSITIVE_WORDS = [
    "rate hike", "hikes rates", "strong", "growth", "beats expectations",
    "surges", "rallies", "optimis", "recovery", "expansion", "hawkish",
]
NEGATIVE_WORDS = [
    "rate cut", "cuts rates", "weak", "recession", "misses expectations",
    "plunges", "falls", "pessimis", "contraction", "slowdown", "dovish",
    "crisis", "inflation surge",
]


def _score_headline(text):
    text = text.lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in text:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in text:
            score -= 1
    return score


def get_currency_sentiment(currency_code):
    """
    Returns a float roughly in [-1, 1]. Positive = bullish news for that
    currency, negative = bearish, 0 = neutral / no data.
    """
    if not config.NEWSAPI_KEY:
        return 0.0

    keywords = CURRENCY_KEYWORDS.get(currency_code, [currency_code])
    query = " OR ".join(f'"{k}"' for k in keywords)

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20,
                "apiKey": config.NEWSAPI_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception as e:
        print(f"[news_sentiment] Warning: could not fetch news for {currency_code}: {e}")
        return 0.0

    if not articles:
        return 0.0

    total = 0
    for a in articles:
        text = f"{a.get('title', '')} {a.get('description', '')}"
        total += _score_headline(text)

    # normalize to roughly [-1, 1]
    normalized = max(-1.0, min(1.0, total / max(len(articles), 1)))
    return normalized


def get_pair_sentiment(instrument):
    """
    instrument like 'EUR_USD' -> returns (base_sentiment, quote_sentiment, net_score)
    net_score > 0 favors buying the pair, < 0 favors selling.
    """
    base, quote = instrument.split("_")
    base_score = get_currency_sentiment(base)
    quote_score = get_currency_sentiment(quote)
    net = base_score - quote_score
    return base_score, quote_score, net
