"""Phase 2: turn a raw cached CSV into a tidy, canonical-schema frame.

Canonical schema (identical across all five assets):
    Date, Open, High, Low, Close, Volume
Date is a plain column (not the index), ascending, no duplicate dates.

No forward-fill, no leakage handling, no indicators here -- that's
Phase 3 (feature_engineering.py).
"""

import pandas as pd

from src.data_fetcher import _cache_path

CANONICAL_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
OHLC_COLUMNS = ["Open", "High", "Low", "Close"]
GAP_THRESHOLD_DAYS = 4


def _load_raw(ticker: str) -> pd.DataFrame:
    path = _cache_path(ticker)
    if not path.exists():
        raise FileNotFoundError(
            f"no cache for {ticker} at {path} -- run scripts/download_data.py first"
        )
    return pd.read_csv(path, parse_dates=["Date"])


def clean(ticker: str) -> tuple[pd.DataFrame, dict]:
    """Clean one ticker's cached CSV.

    Returns (clean_df, qa) where qa reports rows before/after, what was
    dropped and why, and any gap longer than GAP_THRESHOLD_DAYS.
    """
    raw = _load_raw(ticker)
    rows_before = len(raw)

    # Yahoo's Adj Close is not the price column we use -- drop it, keep Close.
    df = raw[CANONICAL_COLUMNS].copy()

    df = df.sort_values("Date")

    before_dedup = len(df)
    df = df.drop_duplicates(subset="Date", keep="first")
    dropped_duplicates = before_dedup - len(df)

    before_dropna = len(df)
    df = df.dropna(subset=OHLC_COLUMNS)  # Volume stays even if NaN (FX)
    dropped_missing_ohlc = before_dropna - len(df)

    df = df.reset_index(drop=True)

    gaps = []
    if len(df) > 1:
        gap_days = df["Date"].diff().dt.days
        for idx in df.index[gap_days > GAP_THRESHOLD_DAYS]:
            gaps.append((
                str(df.loc[idx - 1, "Date"].date()),
                str(df.loc[idx, "Date"].date()),
                int(gap_days.loc[idx]),
            ))

    qa = {
        "ticker": ticker,
        "rows_before": rows_before,
        "rows_after": len(df),
        "dropped_duplicates": dropped_duplicates,
        "dropped_missing_ohlc": dropped_missing_ohlc,
        "date_min": str(df["Date"].min().date()) if len(df) else None,
        "date_max": str(df["Date"].max().date()) if len(df) else None,
        "gaps": gaps,
    }
    return df, qa


def load_clean(ticker: str) -> pd.DataFrame:
    """Public entry point later phases call. Schema-only, no QA payload."""
    df, _ = clean(ticker)
    return df
