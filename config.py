# Watchlist and thresholds. Tune these as you observe live behavior.

from zoneinfo import ZoneInfo

WATCHLIST = ["NVDA", "TSLA", "SPY", "QQQ", "AAPL", "GOOG", "AMZN"]

# How much history to pull per ticker. Needs enough calendar days to cover
# the longer lookback (30 trading days) plus weekends/holidays padding.
FETCH_PERIOD = "6mo"

# Volume spike signal
VOLUME_LOOKBACK_DAYS = 30
VOLUME_SPIKE_MULTIPLIER = 2.0

# ATR move signal
ATR_LOOKBACK_DAYS = 20
ATR_MOVE_MULTIPLIER = 1.5

# JSON export (for the website)
JSON_OUTPUT_PATH = "data/signals.json"

# Market-hours guard. The GitHub Actions cron fires on a broad UTC window;
# this is the authoritative check for whether the market is actually open.
MARKET_TIMEZONE = ZoneInfo("America/New_York")
MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE = 9, 30
MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE = 16, 0
