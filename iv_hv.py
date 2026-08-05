import numpy as np
import pandas as pd

from config import ATR_LOOKBACK_DAYS, IV_HV_HIGH_MULTIPLIER, IV_HV_LOW_MULTIPLIER

TRADING_DAYS_PER_YEAR = 252


def calculate_hv(price_df: pd.DataFrame, window: int = ATR_LOOKBACK_DAYS) -> float:
    """Annualized realized volatility: stdev of daily log returns over the
    trailing window, scaled to a yearly figure so it's comparable to IV.
    """
    closes = price_df["Close"]
    log_returns = np.log(closes / closes.shift(1))
    daily_std = log_returns.iloc[-window:].std()
    return float(daily_std * np.sqrt(TRADING_DAYS_PER_YEAR))


def _atm_iv(chain: pd.DataFrame, spot_price: float) -> float:
    if chain.empty:
        raise ValueError("empty option chain")

    idx = (chain["strike"] - spot_price).abs().idxmin()
    row = chain.loc[idx]

    if row["bid"] <= 0:
        raise ValueError(f"ATM contract (strike {row['strike']}) has no live bid")

    iv = row["impliedVolatility"]
    if iv is None or iv <= 0:
        raise ValueError(f"ATM contract (strike {row['strike']}) has no valid IV")

    return float(iv)


def calculate_atm_iv(calls: pd.DataFrame, puts: pd.DataFrame, spot_price: float) -> float:
    """Average of ATM call and put IV — smooths bid/ask noise; the two
    should be close anyway per put-call parity.
    """
    call_iv = _atm_iv(calls, spot_price)
    put_iv = _atm_iv(puts, spot_price)
    return (call_iv + put_iv) / 2


def calculate_iv_hv_signal(
    price_df: pd.DataFrame, calls: pd.DataFrame, puts: pd.DataFrame, expiry: str
) -> dict:
    spot_price = float(price_df["Close"].iloc[-1])
    iv = calculate_atm_iv(calls, puts, spot_price)
    hv = calculate_hv(price_df)

    ratio = iv / hv
    flagged = ratio > IV_HV_HIGH_MULTIPLIER or ratio < IV_HV_LOW_MULTIPLIER

    return {
        "expiry": expiry,
        "iv": iv,
        "hv": hv,
        "iv_hv_ratio": ratio,
        "iv_hv_flagged": flagged,
    }
