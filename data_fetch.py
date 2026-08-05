from datetime import date, datetime

import pandas as pd
import yfinance as yf

from config import FETCH_PERIOD, OPTIONS_MIN_DAYS_TO_EXPIRY


def fetch_history(ticker: str) -> pd.DataFrame:
    """Pull daily OHLCV history for a ticker. Raises if no data is returned."""
    df = yf.Ticker(ticker).history(period=FETCH_PERIOD)
    if df.empty:
        raise ValueError(f"no data returned for {ticker}")
    return df


def _is_monthly_expiry(expiry: str) -> bool:
    d = datetime.strptime(expiry, "%Y-%m-%d").date()
    return d.weekday() == 4 and 15 <= d.day <= 21


def select_expiry(ticker_obj: yf.Ticker, min_days_to_expiry: int = OPTIONS_MIN_DAYS_TO_EXPIRY) -> str:
    """Pick the nearest standard monthly expiry (3rd Friday) that's far
    enough out to avoid the noise of an about-to-expire contract. Falls
    back to the nearest expiry of any kind if no monthly qualifies.
    """
    expirations = ticker_obj.options
    if not expirations:
        raise ValueError("no option expirations available")

    today = date.today()

    def days_out(expiry: str) -> int:
        return (datetime.strptime(expiry, "%Y-%m-%d").date() - today).days

    monthly = [e for e in expirations if _is_monthly_expiry(e)]
    candidates = monthly if monthly else list(expirations)

    eligible = [e for e in candidates if days_out(e) >= min_days_to_expiry]
    if not eligible:
        raise ValueError(f"no expiry at least {min_days_to_expiry} days out")

    return min(eligible)


def fetch_option_chain(ticker: str) -> tuple[str, pd.DataFrame, pd.DataFrame]:
    """Fetch the calls/puts chain for the nearest suitable monthly expiry."""
    ticker_obj = yf.Ticker(ticker)
    expiry = select_expiry(ticker_obj)
    chain = ticker_obj.option_chain(expiry)
    return expiry, chain.calls, chain.puts
