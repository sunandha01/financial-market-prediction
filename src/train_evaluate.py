"""Phase 4: walk-forward validation of 5 models x 5 assets, plus naive baselines.

TimeSeriesSplit never shuffles and the test window always follows the train
window. Features are the 43 engineered columns only (no Date/OHLCV passthrough).
No model is saved or selected here -- that is Phase 5.
"""

import time
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from config import (ARTIFACTS_DIR, CV_GAP, CV_SPLITS, ELASTICNET_PARAMS, GBR_PARAMS,
                    REPORTS_DIR, RF_PARAMS, TICKERS, XGB_PARAMS)
from src.feature_engineering import NON_FEATURE_COLUMNS, build_dataset
from src.models import get_models
from src.visualize import plot_last_fold

TARGET = "target_ret_7d"
BASELINE_MEAN = "baseline_mean"
BASELINE_SIGN = "baseline_majority_sign"
METRIC_COLS = ["mae", "rmse", "r2", "mape", "dir_acc"]


def _direction_accuracy(y_true: np.ndarray, sign_pred: np.ndarray) -> float:
    nz = y_true != 0  # exact-zero labels have no direction
    return float(np.mean(sign_pred[nz] == np.sign(y_true[nz])))


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    nz = y_true != 0
    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": r2_score(y_true, y_pred),
        # Unstable when true returns are near zero -- read with care.
        "mape": float(np.mean(np.abs(y_true[nz] - y_pred[nz]) / np.abs(y_true[nz]))),
        "dir_acc": _direction_accuracy(y_true, np.sign(y_pred)),
    }


def evaluate_ticker(ticker: str) -> tuple[list[dict], pd.DataFrame]:
    """Returns (fold-level metric rows, last-fold predictions for plotting)."""
    df = build_dataset(ticker)
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLUMNS + [TARGET]]
    X, y, dates = df[feature_cols].to_numpy(), df[TARGET].to_numpy(), df["Date"]

    rows, last_fold_preds = [], None
    splitter = TimeSeriesSplit(n_splits=CV_SPLITS, gap=CV_GAP)
    for fold, (tr, te) in enumerate(splitter.split(X), start=1):
        assert tr.max() < te.min(), "test window must come after train window"
        y_tr, y_te = y[tr], y[te]
        info = {
            "ticker": ticker, "fold": fold, "train_rows": len(tr), "test_rows": len(te),
            "train_end": str(dates.iloc[tr.max()].date()),
            "test_start": str(dates.iloc[te.min()].date()),
            "test_end": str(dates.iloc[te.max()].date()),
        }
        preds = {}

        for name, model in get_models().items():
            model.fit(X[tr], y_tr)
            preds[name] = model.predict(X[te])
            rows.append({**info, "model": name, **_metrics(y_te, preds[name])})

        # Baselines from the training fold only.
        mean_pred = np.full(len(te), y_tr.mean())
        preds[BASELINE_MEAN] = mean_pred
        rows.append({**info, "model": BASELINE_MEAN, **_metrics(y_te, mean_pred)})

        majority_sign = 1.0 if (y_tr > 0).mean() >= 0.5 else -1.0
        rows.append({**info, "model": BASELINE_SIGN,
                     "dir_acc": _direction_accuracy(y_te, np.full(len(te), majority_sign))})

        if fold == CV_SPLITS:
            last_fold_preds = pd.DataFrame(
                {"Date": dates.iloc[te].to_numpy(), "actual": y_te, **preds})

    return rows, last_fold_preds


def run_all() -> pd.DataFrame:
    """Train/score every pair, write artifacts/metrics_cv.csv, plots and the report."""
    start = time.time()
    all_rows = []
    for ticker in TICKERS:
        t0 = time.time()
        rows, last_fold = evaluate_ticker(ticker)
        all_rows += rows
        plot_last_fold(ticker, last_fold)
        print(f"[OK] {ticker} done in {time.time() - t0:.1f}s")

    metrics = pd.DataFrame(all_rows)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(ARTIFACTS_DIR / "metrics_cv.csv", index=False)
    runtime = time.time() - start
    _write_report(metrics, runtime)
    print(f"\nWrote {ARTIFACTS_DIR / 'metrics_cv.csv'}")
    print(f"Wrote {REPORTS_DIR / 'phase4_cv.md'}")
    print(f"Total runtime: {runtime:.1f}s")
    return metrics


def _md_table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def _write_report(metrics: pd.DataFrame, runtime: float) -> None:
    mean = metrics.groupby(["ticker", "model"], sort=False)[METRIC_COLS].mean()
    model_names = [m for m in metrics["model"].unique()
                   if m not in (BASELINE_MEAN, BASELINE_SIGN)]

    lines = [
        "# Phase 4 — Walk-forward validation report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}  ·  "
        f"runtime: {runtime:.0f}s",
        "",
        f"`TimeSeriesSplit(n_splits={CV_SPLITS}, gap={CV_GAP})` — no shuffling, test window "
        f"always after train window. The gap purges {CV_GAP} rows between train and test "
        "because 7-day targets of the last train rows overlap the test period. "
        "Features: the 43 engineered columns (no Date/OHLCV). Target: `target_ret_7d`.",
        "",
        f"Settings: RF n_estimators={RF_PARAMS['n_estimators']}, "
        f"XGB n_estimators={XGB_PARAMS['n_estimators']}, "
        f"GBR n_estimators={GBR_PARAMS['n_estimators']}, "
        f"ElasticNet alpha={ELASTICNET_PARAMS['alpha']}. "
        "Metals are COMEX futures (`GC=F`, `SI=F`), not MCX spot.",
        "",
        "Values are means over the folds. Baselines: `baseline_mean` predicts the "
        "training-fold mean return; `baseline_majority_sign` predicts the training-fold "
        "majority direction (direction accuracy only). MAPE is unstable when true returns "
        "are close to zero.",
        "",
    ]

    beat_rmse = beat_dir = pairs = 0
    for ticker in TICKERS:
        base = mean.loc[(ticker, BASELINE_MEAN)]
        sign_dir = mean.loc[(ticker, BASELINE_SIGN), "dir_acc"]
        table = []
        for model in model_names + [BASELINE_MEAN, BASELINE_SIGN]:
            m = mean.loc[(ticker, model)]
            is_model = model in model_names
            beats_rmse = is_model and m["rmse"] < base["rmse"]
            beats_dir = is_model and m["dir_acc"] > max(sign_dir, base["dir_acc"])
            if is_model:
                pairs += 1
                beat_rmse += beats_rmse
                beat_dir += beats_dir
            table.append([
                model,
                *(f"{m[c]:.4f}" if pd.notna(m[c]) else "–" for c in METRIC_COLS),
                ("yes" if beats_rmse else "no") if is_model else "",
                ("yes" if beats_dir else "no") if is_model else "",
            ])
        lines += [f"## {ticker}", ""]
        lines += _md_table(
            ["model", "MAE", "RMSE", "R²", "MAPE", "dir. acc.",
             "beats mean (RMSE)", "beats naive direction"], table)
        lines.append("")

    lines += [
        "## Did the models beat the naive baselines?",
        "",
        f"- Lower mean RMSE than `baseline_mean`: **{beat_rmse} of {pairs}** model×asset pairs",
        f"- Higher direction accuracy than both baselines: **{beat_dir} of {pairs}** pairs",
        "",
        "Fold-level scores (including baselines) are in `artifacts/metrics_cv.csv`. "
        "Plots of the last fold are in `artifacts/plots/`. Accuracy may be modest; "
        "no winner is picked here (Phase 5).",
    ]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "phase4_cv.md").write_text("\n".join(lines) + "\n")
