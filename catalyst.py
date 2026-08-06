import re
from datetime import datetime, timedelta

from config import MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE, TICKER_COMPANY_NAMES


def previous_market_close(now: datetime) -> datetime:
    """The most recent prior trading day's close, in `now`'s timezone.
    Assumes `now` falls within today's market hours (main.py already gates
    on that), so this always looks back at least one day -- never today.
    """
    candidate = (now - timedelta(days=1)).replace(
        hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0
    )
    while candidate.weekday() >= 5:  # Saturday, Sunday
        candidate -= timedelta(days=1)
    return candidate


def _matches_ticker(title: str, ticker: str, aliases: list[str]) -> bool:
    if re.search(rf"\b{re.escape(ticker)}\b", title, re.IGNORECASE):
        return True
    title_lower = title.lower()
    return any(alias.lower() in title_lower for alias in aliases)


def find_catalyst(
    ticker: str, news_items: list[dict], window_start: datetime, window_end: datetime
) -> dict | None:
    """Most recent headline whose title names this ticker/company and
    whose publish time falls in [window_start, window_end]. Returns None
    if nothing matches both conditions -- callers should show an explicit
    "no clear catalyst" state, never guess.
    """
    aliases = TICKER_COMPANY_NAMES.get(ticker, [])
    matches = []

    for item in news_items:
        content = item.get("content", {})
        title = content.get("title")
        pub_date_str = content.get("pubDate")
        if not title or not pub_date_str:
            continue

        pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        if not (window_start <= pub_date <= window_end):
            continue
        if not _matches_ticker(title, ticker, aliases):
            continue

        matches.append((pub_date, content))

    if not matches:
        return None

    matches.sort(key=lambda m: m[0], reverse=True)
    pub_date, content = matches[0]

    url = content.get("canonicalUrl", {}).get("url") or content.get("clickThroughUrl", {}).get("url")
    source = content.get("provider", {}).get("displayName", "Unknown source")

    return {
        "headline": content["title"],
        "source": source,
        "url": url,
        "pub_date": pub_date.isoformat(),
    }
