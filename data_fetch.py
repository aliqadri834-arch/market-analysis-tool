import pandas as pd
import yfinance as yf

from config import FETCH_PERIOD


def fetch_history(ticker: str) -> pd.DataFrame:
    """Pull daily OHLCV history for a ticker. Raises if no data is returned."""
    df = yf.Ticker(ticker).history(period=FETCH_PERIOD)
    if df.empty:
        raise ValueError(f"no data returned for {ticker}")
    return df
