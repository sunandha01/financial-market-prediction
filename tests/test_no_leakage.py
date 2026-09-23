"""Phase 3 leakage checks. No pytest -- run directly:

    python tests/test_no_leakage.py

Two independent checks:
1. Static: the source of feature_engineering.py contains exactly one
   negative shift, and it belongs to the target line, not a feature.
2. Data-driven: appending more rows to the raw series must not change
   any already-computed feature value (proves no feature peeks ahead).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config import TICKERS
from src.preprocess import load_clean
from src.feature_engineering import _add_features, build_dataset

FEATURE_ENGINEERING_SRC = (
    Path(__file__).resolve().parent.parent / "src" / "feature_engineering.py"
).read_text()


def test_only_the_target_uses_a_negative_shift():
    # Only real code lines -- comments/docstrings may mention "shift(-"
    # in prose without it being an actual leakage risk.
    matches = [
        line for line in FEATURE_ENGINEERING_SRC.splitlines()
        if re.search(r"shift\(\s*-", line) and not line.strip().startswith("#")
    ]
    assert matches, "expected at least one negative shift (the target), found none"
    assert all("target_ret_7d" in m for m in matches), (
        f"a negative shift outside the target line was found: {matches}"
    )


def test_features_do_not_use_future_rows():
    # Any ticker works; GC=F has the fewest cached rows so it's fastest.
    ticker = "GC=F"
    clean = load_clean(ticker)

    cutoff = len(clean) - 30  # well past every warmup window (max window = 50)
    assert cutoff > 60, "cached history too short for this leakage check"

    full = _add_features(clean)
    truncated = _add_features(clean.iloc[: cutoff + 1].reset_index(drop=True))

    feature_cols = [c for c in full.columns if c not in
                    ("Date", "Open", "High", "Low", "Close", "Volume")]

    row_if_future_seen = full.iloc[cutoff][feature_cols]
    row_if_future_unseen = truncated.iloc[-1][feature_cols]

    pd.testing.assert_series_equal(
        row_if_future_seen, row_if_future_unseen, check_names=False,
        obj="feature row at the cutoff date, with vs without future rows",
    )


def test_build_dataset_has_no_nans_for_any_ticker():
    for ticker in TICKERS:
        df = build_dataset(ticker)
        assert df.isna().sum().sum() == 0, f"{ticker}: NaNs remain after warmup/target drop"
        assert "target_ret_7d" in df.columns


if __name__ == "__main__":
    test_only_the_target_uses_a_negative_shift()
    test_features_do_not_use_future_rows()
    test_build_dataset_has_no_nans_for_any_ticker()
    print("All Phase 3 leakage checks passed.")
