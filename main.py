from datetime import datetime

from catalyst import find_catalyst, previous_market_close
from config import (
    JSON_OUTPUT_PATH,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_TIMEZONE,
    WATCHLIST,
)
from data_fetch import fetch_history, fetch_news, fetch_option_chain
from export_json import write_json
from iv_hv import calculate_iv_hv_signal
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


def _is_flagged(record: dict) -> bool:
    if record["signals"] is not None:
        if record["signals"]["volume_flagged"] or record["signals"]["atr_flagged"]:
            return True
    if record["iv_hv"] is not None and record["iv_hv"]["iv_hv_flagged"]:
        return True
    return False


def analyze_ticker(ticker: str, now: datetime) -> dict:
    record = {
        "ticker": ticker,
        "signals": None,
        "error": None,
        "iv_hv": None,
        "iv_hv_error": None,
        "catalyst_status": "not_flagged",
        "catalyst": None,
        "catalyst_error": None,
    }

    try:
        df = fetch_history(ticker)
        record["signals"] = calculate_signals(df)
    except Exception as e:
        record["error"] = e
        return record

    try:
        expiry, calls, puts = fetch_option_chain(ticker)
        record["iv_hv"] = calculate_iv_hv_signal(df, calls, puts, expiry)
    except Exception as e:
        record["iv_hv_error"] = e

    if _is_flagged(record):
        try:
            news_items = fetch_news(ticker)
            window_start = previous_market_close(now)
            catalyst = find_catalyst(ticker, news_items, window_start, now)
            if catalyst is not None:
                record["catalyst_status"] = "found"
                record["catalyst"] = catalyst
            else:
                record["catalyst_status"] = "unclear"
        except Exception as e:
            record["catalyst_status"] = "error"
            record["catalyst_error"] = str(e)

    return record


def main() -> None:
    now = datetime.now(MARKET_TIMEZONE)
    if not market_is_open(now):
        print(f"Market closed at {now.isoformat()} — skipping run.")
        return

    results = [analyze_ticker(ticker, now) for ticker in WATCHLIST]

    print_report(results)
    write_json(results, JSON_OUTPUT_PATH)


if __name__ == "__main__":
    main()
