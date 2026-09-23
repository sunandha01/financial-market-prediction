"""Phase 6: pure inference. predict(ticker, as_of=None) -> dict.

Loads the Phase 5 winner for the ticker; never refits, never runs CV, never
calls Yahoo (reads the data/ cache via load_clean). Deterministic: same cache
+ same model file -> same dict.

Experimental, not investment advice. Per reports/phase5_selection.md every
saved winner loses to baseline_mean on RMSE, and only GBPUSD=X beats both
direction baselines -- read beats_baseline_* before trusting any number.
Metals (GC=F, SI=F) are COMEX futures, not MCX spot. If as_of falls inside the
training period the prediction is in-sample, not a real forecast.

CLI:
    python -m src.predict GC=F
    python -m src.predict GC=F --as-of 2026-06-30
"""

import argparse
import json

import joblib
import pandas as pd

from config import ARTIFACTS_DIR, BASE_DIR, MODELS_DIR, TICKERS
from src.data_fetcher import _cache_path
from src.feature_engineering import build_features

SUMMARY_CSV = ARTIFACTS_DIR / "metrics_summary.csv"


def _winner_row(ticker: str) -> pd.Series:
    if ticker not in TICKERS:
        raise ValueError(f"unknown ticker {ticker!r}; expected one of {list(TICKERS)}")
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"{SUMMARY_CSV} missing -- run scripts/select_models.py (Phase 5)")
    summary = pd.read_csv(SUMMARY_CSV).set_index("ticker")
    return summary.loc[ticker]


def _direction(pred: float) -> str:
    return "up" if pred > 0 else "down" if pred < 0 else "flat"


def predict(ticker: str, as_of: str | None = None) -> dict:
    """Forecast the 7-day forward return using the last feature row dated <= as_of
    (latest row if as_of is None). Returned `as_of` is the date of the row used."""
    win = _winner_row(ticker)
    model_path = MODELS_DIR / f"{_cache_path(ticker).stem}_{win['winner']}.joblib"
    bundle = joblib.load(model_path)

    feats = build_features(ticker)  # raises FileNotFoundError if the cache is missing
    if as_of is not None:
        feats = feats[feats["Date"] <= pd.Timestamp(as_of)]
        if feats.empty:
            raise ValueError(f"no feature row for {ticker} on or before {as_of}")
    row = feats.iloc[-1]

    # Exact training column order, taken from the saved bundle.
    X = row[bundle["feature_columns"]].to_numpy(dtype=float).reshape(1, -1)
    pred = float(bundle["model"].predict(X)[0])

    return {
        "ticker": ticker,
        "as_of": str(row["Date"].date()),
        "pred_return_7d": pred,
        "direction": _direction(pred),
        "model_name": bundle["model_name"],
        "model_path": model_path.relative_to(BASE_DIR).as_posix(),
        "last_close": float(row["Close"]),
        "beats_baseline_rmse": bool(win["beats_baseline_mean_rmse"]),
        "beats_baseline_direction": bool(win["beats_both_direction_baselines"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="7-day return forecast (experimental, not advice)")
    parser.add_argument("ticker", help=f"one of {list(TICKERS)}")
    parser.add_argument("--as-of", help="YYYY-MM-DD; default = latest cached row")
    args = parser.parse_args()
    print(json.dumps(predict(args.ticker, args.as_of), indent=2))


if __name__ == "__main__":
    main()
