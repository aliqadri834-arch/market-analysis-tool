import pandas as pd

from config import (
    ATR_LOOKBACK_DAYS,
    ATR_MOVE_MULTIPLIER,
    VOLUME_LOOKBACK_DAYS,
    VOLUME_SPIKE_MULTIPLIER,
)

MIN_ROWS_REQUIRED = max(VOLUME_LOOKBACK_DAYS, ATR_LOOKBACK_DAYS) + 2


def calculate_volume_signal(df: pd.DataFrame) -> dict:
    """Flag if today's volume is more than VOLUME_SPIKE_MULTIPLIER x the
    trailing VOLUME_LOOKBACK_DAYS average (today excluded from the average).
    """
    today_volume = df["Volume"].iloc[-1]
    baseline = df["Volume"].iloc[-(VOLUME_LOOKBACK_DAYS + 1) : -1]
    avg_volume = baseline.mean()

    ratio = today_volume / avg_volume
    flagged = ratio > VOLUME_SPIKE_MULTIPLIER

    return {
        "today_volume": today_volume,
        "avg_volume": avg_volume,
        "volume_ratio": ratio,
        "volume_flagged": flagged,
    }


def _true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - prev_close).abs()
    low_prev_close = (df["Low"] - prev_close).abs()
    return pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)


def calculate_atr_signal(df: pd.DataFrame) -> dict:
    """Flag if today's close-to-close move exceeds ATR_MOVE_MULTIPLIER x the
    ATR_LOOKBACK_DAYS average true range (today's own range excluded from
    the ATR baseline, since we're comparing today against a "normal" bar).
    """
    tr = _true_range(df)
    atr = tr.iloc[-(ATR_LOOKBACK_DAYS + 1) : -1].mean()

    today_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]
    move = today_close - prev_close
    move_in_atr_units = move / atr

    flagged = abs(move) > ATR_MOVE_MULTIPLIER * atr

    return {
        "close": today_close,
        "move": move,
        "atr": atr,
        "move_in_atr_units": move_in_atr_units,
        "atr_flagged": flagged,
    }


def calculate_signals(df: pd.DataFrame) -> dict:
    if len(df) < MIN_ROWS_REQUIRED:
        raise ValueError(
            f"not enough history: got {len(df)} rows, need at least {MIN_ROWS_REQUIRED}"
        )

    result = {}
    result.update(calculate_volume_signal(df))
    result.update(calculate_atr_signal(df))
    return result
