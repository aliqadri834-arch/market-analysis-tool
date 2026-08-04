from datetime import datetime

from config import (
    JSON_OUTPUT_PATH,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_TIMEZONE,
    WATCHLIST,
)
from data_fetch import fetch_history
from export_json import write_json
from report import print_report
from signals import calculate_signals


def market_is_open(now: datetime) -> bool:
    if now.weekday() >= 5:  # Saturday, Sunday
        return False

    open_time = now.replace(
        hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0
    )
    close_time = now.replace(
        hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0
    )
    return open_time <= now <= close_time


def main() -> None:
    now = datetime.now(MARKET_TIMEZONE)
    if not market_is_open(now):
        print(f"Market closed at {now.isoformat()} — skipping run.")
        return

    results = []
    for ticker in WATCHLIST:
        try:
            df = fetch_history(ticker)
            signals = calculate_signals(df)
            results.append((ticker, signals, None))
        except Exception as e:
            results.append((ticker, None, e))

    print_report(results)
    write_json(results, JSON_OUTPUT_PATH)


if __name__ == "__main__":
    main()
