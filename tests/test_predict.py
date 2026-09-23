"""Phase 6 checks. No pytest -- run directly:

    python tests/test_predict.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd

from config import BASE_DIR, TICKERS
from src.feature_engineering import build_dataset, build_features
from src.predict import predict

KEYS = {"ticker", "as_of", "pred_return_7d", "direction", "model_name", "model_path",
        "last_close", "beats_baseline_rmse", "beats_baseline_direction"}


def test_keys_and_determinism():
    for ticker in TICKERS:
        a, b = predict(ticker), predict(ticker)
        assert set(a) == KEYS, f"{ticker}: {set(a) ^ KEYS}"
        assert a == b, f"{ticker}: two calls differ"
        assert a["direction"] in ("up", "down", "flat")


def test_as_of_uses_last_row_on_or_before():
    # 2026-09-20 is a Sunday: the row used must be an earlier session, never a later one.
    r = predict("GC=F", as_of="2026-09-20")
    assert r["as_of"] <= "2026-09-20"
    assert r["as_of"] == str(build_features("GC=F").query("Date <= '2026-09-20'")["Date"].iloc[-1].date())


def test_inference_row_matches_training_row():
    # A date that exists in the training table must give identical feature values
    # from build_features (inference) and build_dataset (training).
    train = build_dataset("GC=F")
    row_date = train["Date"].iloc[-50]
    feats = build_features("GC=F").set_index("Date")
    cols = joblib.load(BASE_DIR / predict("GC=F")["model_path"])["feature_columns"]
    pd.testing.assert_series_equal(
        feats.loc[row_date, cols], train.set_index("Date").loc[row_date, cols], check_names=False)


def test_bad_inputs_raise():
    for bad in (lambda: predict("NOPE"), lambda: predict("GC=F", as_of="1990-01-01")):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_keys_and_determinism()
    test_as_of_uses_last_row_on_or_before()
    test_inference_row_matches_training_row()
    test_bad_inputs_raise()
    print("All Phase 6 predict checks passed.")
