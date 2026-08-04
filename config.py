# Watchlist and thresholds. Tune these as you observe live behavior.

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
