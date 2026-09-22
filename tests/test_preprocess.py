"""Phase 2 schema/QA checks. No pytest -- run directly:

    python tests/test_preprocess.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TICKERS
from src.preprocess import load_clean, CANONICAL_COLUMNS


def test_schema_identical_across_assets():
    for ticker in TICKERS:
        df = load_clean(ticker)
        assert list(df.columns) == CANONICAL_COLUMNS, f"{ticker}: {list(df.columns)}"


def test_sorted_ascending_no_duplicate_dates():
    for ticker in TICKERS:
        df = load_clean(ticker)
        assert df["Date"].is_monotonic_increasing, f"{ticker}: not sorted ascending"
        assert df["Date"].duplicated().sum() == 0, f"{ticker}: duplicate dates remain"


def test_no_missing_ohlc():
    for ticker in TICKERS:
        df = load_clean(ticker)
        assert df[["Open", "High", "Low", "Close"]].isna().sum().sum() == 0, (
            f"{ticker}: missing OHLC values remain"
        )


def test_volume_column_kept():
    for ticker in TICKERS:
        df = load_clean(ticker)
        assert "Volume" in df.columns, f"{ticker}: Volume column dropped"


if __name__ == "__main__":
    test_schema_identical_across_assets()
    test_sorted_ascending_no_duplicate_dates()
    test_no_missing_ohlc()
    test_volume_column_kept()
    print("All Phase 2 schema checks passed.")
