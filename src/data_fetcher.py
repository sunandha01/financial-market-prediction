"""Phase 1: download and cache daily OHLCV for one ticker via yfinance.

No cleaning here beyond flattening yfinance's multi-level columns --
that belongs to Phase 2 (src/preprocess.py).
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

from config import START_DATE, END_DATE, DATA_DIR

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _cache_path(ticker: str) -> Path:
    # "=" and other symbol chars are filesystem-safe here, but normalize
    # anyway so cache filenames stay predictable across platforms.
    safe = ticker.replace("=", "_").replace("/", "_")
    return DATA_DIR / f"{safe}.csv"


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance returns MultiIndex columns (field, ticker) for some calls.
    Collapse to the field name only."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_ticker(ticker: str, force: bool = False) -> dict:
    """Download (or reuse cache for) one ticker.

    Returns a result dict: ticker, rows, start, end, cached, error (or None).
    Never raises -- caller loops over tickers and this must not kill the run.
    """
    path = _cache_path(ticker)
    result = {"ticker": ticker, "rows": 0, "start": None, "end": None,
              "cached": False, "error": None, "missing_columns": []}

    if path.exists() and not force:
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            result["cached"] = True
        except Exception as exc:  # corrupt cache -- fall through to re-download
            result["error"] = f"cache read failed, re-downloading: {exc}"
            df = None
    else:
        df = None

    if df is None:
        try:
            df = yf.download(ticker, start=START_DATE, end=END_DATE,
                              auto_adjust=False, progress=False)
            df = _flatten_columns(df)
            if df.empty:
                result["error"] = "empty download (no data returned)"
                return result
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(path)
        except Exception as exc:
            result["error"] = f"download failed: {exc}"
            return result

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    result["missing_columns"] = missing
    result["rows"] = len(df)
    if len(df):
        result["start"] = str(df.index.min().date())
        result["end"] = str(df.index.max().date())
    return result
