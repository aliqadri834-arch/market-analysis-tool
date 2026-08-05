"""One-off research script: do the volume-spike and ATR-move flags used in
main.py actually predict anything about forward returns?

Not part of the scheduled pipeline -- run manually with `python backtest.py`.
Reuses the same threshold constants as signals.py (via config.py) but
recomputes them as rolling/vectorized series across history rather than a
single point-in-time check, since that's what a backtest needs.
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from config import (
    ATR_LOOKBACK_DAYS,
    ATR_MOVE_MULTIPLIER,
    VOLUME_LOOKBACK_DAYS,
    VOLUME_SPIKE_MULTIPLIER,
    WATCHLIST,
)

CACHE_PATH = Path("backtest_cache.pkl")
FETCH_PERIOD = "9mo"  # ~6mo analysis window + lead-in for the rolling windows
ANALYSIS_MONTHS = 6
HORIZONS = (1, 3, 5)


def fetch_data(use_cache: bool = True) -> dict[str, pd.DataFrame]:
    """One batched call for all tickers, cached to disk so repeated runs
    while tuning the analysis don't keep re-hitting yfinance.
    """
    if use_cache and CACHE_PATH.exists():
        with CACHE_PATH.open("rb") as f:
            return pickle.load(f)

    raw = yf.download(WATCHLIST, period=FETCH_PERIOD, group_by="ticker", progress=False)
    data = {ticker: raw[ticker].dropna(how="all") for ticker in WATCHLIST}

    with CACHE_PATH.open("wb") as f:
        pickle.dump(data, f)

    return data


def compute_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling version of the same volume/ATR flag logic in signals.py.
    Each day's flag uses only prior days (shift(1) after the rolling
    window), matching the "today vs trailing window excluding today"
    definition used live.
    """
    df = df.copy()

    avg_volume = df["Volume"].rolling(VOLUME_LOOKBACK_DAYS).mean().shift(1)
    df["volume_ratio"] = df["Volume"] / avg_volume
    df["volume_flagged"] = df["volume_ratio"] > VOLUME_SPIKE_MULTIPLIER

    prev_close = df["Close"].shift(1)
    true_range = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(ATR_LOOKBACK_DAYS).mean().shift(1)
    move = df["Close"] - prev_close
    df["move_atr_ratio"] = move / atr
    df["atr_flagged"] = move.abs() > ATR_MOVE_MULTIPLIER * atr

    for n in HORIZONS:
        df[f"fwd_ret_{n}d"] = df["Close"].shift(-n) / df["Close"] - 1

    return df


def build_dataset() -> pd.DataFrame:
    raw = fetch_data()

    frames = []
    for ticker, df in raw.items():
        flagged = compute_flags(df).reset_index()
        flagged = flagged.rename(columns={flagged.columns[0]: "date"})
        flagged["ticker"] = ticker
        frames.append(flagged)

    pooled = pd.concat(frames, ignore_index=True)

    cutoff = pooled["date"].max() - pd.DateOffset(months=ANALYSIS_MONTHS)
    return pooled[pooled["date"] >= cutoff].reset_index(drop=True)


def summarize_group(df: pd.DataFrame, mask: pd.Series) -> dict:
    subset = df[mask]
    row = {"n": len(subset)}
    for n in HORIZONS:
        vals = subset[f"fwd_ret_{n}d"].dropna()
        row[f"avg_{n}d"] = vals.mean() if len(vals) else float("nan")
        row[f"std_{n}d"] = vals.std() if len(vals) else float("nan")
    return row


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    either = df["volume_flagged"] | df["atr_flagged"]
    groups = {
        "Volume flagged": df["volume_flagged"],
        "Volume unflagged": ~df["volume_flagged"],
        "ATR flagged": df["atr_flagged"],
        "ATR unflagged": ~df["atr_flagged"],
        "Either flagged": either,
        "Neither flagged": ~either,
    }
    rows = {label: summarize_group(df, mask) for label, mask in groups.items()}
    return pd.DataFrame(rows).T


def build_per_ticker_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    either = df["volume_flagged"] | df["atr_flagged"]
    rows = {}
    for ticker, ticker_df in df.groupby("ticker"):
        ticker_either = either[ticker_df.index]
        flagged_ret = ticker_df.loc[ticker_either, "fwd_ret_3d"].dropna()
        unflagged_ret = ticker_df.loc[~ticker_either, "fwd_ret_3d"].dropna()
        rows[ticker] = {
            "n_flagged": int(ticker_either.sum()),
            "avg_3d_flagged": flagged_ret.mean() if len(flagged_ret) else float("nan"),
            "n_unflagged": int((~ticker_either).sum()),
            "avg_3d_unflagged": unflagged_ret.mean() if len(unflagged_ret) else float("nan"),
        }
    return pd.DataFrame(rows).T


def _fmt_pct(x: float) -> str:
    return "n/a" if pd.isna(x) else f"{x:+.2%}"


def print_summary(summary: pd.DataFrame) -> None:
    header = f"{'Signal':<18}{'N':>6}" + "".join(
        f"{'Avg ' + str(n) + 'd':>12}{'Std ' + str(n) + 'd':>12}" for n in HORIZONS
    )
    print(header)
    print("-" * len(header))
    for label, row in summary.iterrows():
        line = f"{label:<18}{int(row['n']):>6}"
        for n in HORIZONS:
            line += f"{_fmt_pct(row[f'avg_{n}d']):>12}{_fmt_pct(row[f'std_{n}d']):>12}"
        print(line)


def print_per_ticker(breakdown: pd.DataFrame) -> None:
    print()
    print("Per-ticker breakdown (either flag, 3-day forward return) -- very low n, directional only:")
    header = f"{'Ticker':<8}{'N flagged':>11}{'Avg 3d':>12}{'N unflagged':>13}{'Avg 3d':>12}"
    print(header)
    print("-" * len(header))
    for ticker, row in breakdown.iterrows():
        print(
            f"{ticker:<8}{int(row['n_flagged']):>11}{_fmt_pct(row['avg_3d_flagged']):>12}"
            f"{int(row['n_unflagged']):>13}{_fmt_pct(row['avg_3d_unflagged']):>12}"
        )


def main() -> None:
    df = build_dataset()
    summary = build_summary(df)
    breakdown = build_per_ticker_breakdown(df)

    print_summary(summary)
    print_per_ticker(breakdown)

    n_either = int((df["volume_flagged"] | df["atr_flagged"]).sum())
    print()
    print(
        f"Caveat: {n_either} flagged occurrences pooled across {len(WATCHLIST)} tickers "
        f"over ~{ANALYSIS_MONTHS} months. Read directionally only -- this is not a "
        f"statistically robust sample; do not treat it as validated alpha."
    )


if __name__ == "__main__":
    main()
