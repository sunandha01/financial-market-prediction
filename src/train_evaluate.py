"""Phase 4-5: walk-forward validation of 5 models x 5 assets, plus naive baselines.

Phase 4 (run_all): TimeSeriesSplit never shuffles and the test window always
follows the train window. Features are the 43 engineered columns only (no
Date/OHLCV passthrough).

Phase 5 (select_and_save): pick one winner per asset from the saved CV scores,
refit it on all labelled rows, dump it with joblib. See the SELECTION RULE below.
"""

import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from config import (ARTIFACTS_DIR, CV_GAP, CV_SPLITS, ELASTICNET_PARAMS, GBR_PARAMS,
                    MODELS_DIR, REPORTS_DIR, RF_PARAMS, TICKERS, XGB_PARAMS)
from src.data_fetcher import _cache_path
from src.feature_engineering import NON_FEATURE_COLUMNS, build_dataset
from src.models import get_models
from src.visualize import plot_importance, plot_last_fold

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


def _feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_FEATURE_COLUMNS + [TARGET]]


def evaluate_ticker(ticker: str) -> tuple[list[dict], pd.DataFrame]:
    """Returns (fold-level metric rows, last-fold predictions for plotting)."""
    df = build_dataset(ticker)
    feature_cols = _feature_columns(df)
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


# ---------------------------------------------------------------------------
# Phase 5: model selection + artefacts
# ---------------------------------------------------------------------------
#
# SELECTION RULE (do not change silently):
#   Candidates = the five ML models only; baselines are never saved.
#   Winner per asset = highest MEAN directional accuracy across the 5 CV folds;
#   tie (compared at 6 decimals) -> lower MEAN RMSE.
#
# Facts from the Phase 4 run that this rule does NOT fix -- keep them visible:
#   * 0 of 25 model x asset pairs beat baseline_mean on RMSE.
#   * 5 of 25 beat BOTH direction baselines, and all five are GBPUSD=X.
#   * Gold/silver naive direction accuracy is high because both drifted upward
#     over 2019-2026; a model has to beat that drift, and none does.
#   * The winner is the best of five scored on the same folds, so its score is
#     biased upward. A saved winner is not evidence of forecasting skill.
#   * No 60-65% accuracy claim exists anywhere in the metrics; do not make one.

TREE_MODELS = {"random_forest", "xgboost", "gradient_boosting"}
ML_MODELS = ["random_forest", "xgboost", "ridge", "elasticnet", "gradient_boosting"]


def _safe_ticker(ticker: str) -> str:
    return _cache_path(ticker).stem  # same convention as the data/ cache files


def _beats_naive(mean: pd.DataFrame, ticker: str, model: str) -> tuple[bool, bool]:
    """(beats baseline_mean on RMSE, beats BOTH direction baselines)."""
    m = mean.loc[(ticker, model)]
    beats_rmse = bool(m["rmse"] < mean.loc[(ticker, BASELINE_MEAN), "rmse"])
    naive_dir = max(mean.loc[(ticker, BASELINE_MEAN), "dir_acc"],
                    mean.loc[(ticker, BASELINE_SIGN), "dir_acc"])
    return beats_rmse, bool(m["dir_acc"] > naive_dir)


def select_winners(metrics: pd.DataFrame) -> pd.DataFrame:
    """One row per asset: the winning ML model next to both naive baselines."""
    mean = metrics.groupby(["ticker", "model"], sort=False)[METRIC_COLS].mean()
    rows = []
    for ticker in TICKERS:
        cand = mean.loc[ticker].loc[ML_MODELS].copy()
        cand["dir_key"] = cand["dir_acc"].round(6)
        cand = cand.sort_values(["dir_key", "rmse"], ascending=[False, True])
        winner = cand.index[0]
        w = cand.iloc[0]
        beats_rmse, beats_dir = _beats_naive(mean, ticker, winner)
        rows.append({
            "ticker": ticker, "winner": winner,
            "dir_acc": w["dir_acc"], "rmse": w["rmse"], "mae": w["mae"],
            "r2": w["r2"], "mape": w["mape"],
            "baseline_mean_dir_acc": mean.loc[(ticker, BASELINE_MEAN), "dir_acc"],
            "baseline_mean_rmse": mean.loc[(ticker, BASELINE_MEAN), "rmse"],
            "baseline_majority_sign_dir_acc": mean.loc[(ticker, BASELINE_SIGN), "dir_acc"],
            "beats_baseline_mean_rmse": beats_rmse,
            "beats_both_direction_baselines": beats_dir,
        })
    return pd.DataFrame(rows)


def _fit_winner(ticker: str, model_name: str):
    """Refit on every labelled row. build_dataset already drops the last 7
    sessions (no 7-day-ahead close), so no future target is used."""
    df = build_dataset(ticker)
    feature_cols = _feature_columns(df)
    model = get_models()[model_name]
    model.fit(df[feature_cols].to_numpy(), df[TARGET].to_numpy())
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{_safe_ticker(ticker)}_{model_name}.joblib"
    joblib.dump({
        "model": model, "model_name": model_name, "ticker": ticker,
        "feature_columns": feature_cols, "train_rows": len(df),
        "train_end": str(df["Date"].iloc[-1].date()),
    }, path)
    importance = None
    if model_name in TREE_MODELS:
        importance = pd.DataFrame({
            "ticker": ticker, "model": model_name, "feature": feature_cols,
            "importance": model.feature_importances_,
        }).sort_values("importance", ascending=False)
        plot_importance(ticker, model_name, importance)
    return path, importance


def select_and_save() -> pd.DataFrame:
    csv = ARTIFACTS_DIR / "metrics_cv.csv"
    if not csv.exists():
        raise FileNotFoundError(f"{csv} missing -- run scripts/run_pipeline.py (Phase 4) first")
    metrics = pd.read_csv(csv)
    summary = select_winners(metrics)

    importances = []
    for ticker, model_name in zip(summary["ticker"], summary["winner"]):
        path, imp = _fit_winner(ticker, model_name)
        if imp is not None:
            importances.append(imp)
        print(f"[OK] {ticker}: winner={model_name} -> {path.relative_to(path.parents[2])}")

    summary.to_csv(ARTIFACTS_DIR / "metrics_summary.csv", index=False)
    if importances:
        pd.concat(importances).to_csv(ARTIFACTS_DIR / "feature_importance.csv", index=False)
    _write_selection_report(summary, metrics)
    print(f"\nWrote {ARTIFACTS_DIR / 'metrics_summary.csv'}")
    print(f"Wrote {REPORTS_DIR / 'phase5_selection.md'}")
    return summary


def _write_selection_report(summary: pd.DataFrame, metrics: pd.DataFrame) -> None:
    mean = metrics.groupby(["ticker", "model"], sort=False)[METRIC_COLS].mean()

    # Phase 4 facts, recomputed from the CSV so the report cannot drift from it.
    pairs = [(t, m, *_beats_naive(mean, t, m)) for t in TICKERS for m in ML_MODELS]
    n_rmse = sum(p[2] for p in pairs)
    dir_winners = sorted({p[0] for p in pairs if p[3]})
    n_dir = sum(p[3] for p in pairs)
    ml = mean.reset_index().query("model in @ML_MODELS")
    dir_lo, dir_hi = ml["dir_acc"].min(), ml["dir_acc"].max()
    r2_note = ("every model has negative mean R², meaning it predicts worse than a constant"
               if (ml["r2"] < 0).all() else "some models have positive mean R²")

    lines = [
        "# Phase 5 — Model selection report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Selection rule",
        "",
        "Among the five ML models only (baselines are never saved): highest **mean "
        "directional accuracy** across the 5 walk-forward folds; ties (at 6 decimals) "
        "are broken by lower **mean RMSE**. The winning algorithm is then refit on all "
        "labelled rows (everything except the last 7 sessions, which have no 7-day-ahead "
        "close) and saved to `artifacts/models/`. Scores are from Phase 4 "
        "(`TimeSeriesSplit(5, gap=7)`); features and CV settings are unchanged.",
        "",
        "## Winner vs the naive baselines",
        "",
    ]
    table = []
    for r in summary.itertuples():
        table.append([
            r.ticker, r.winner,
            f"{r.dir_acc:.4f}", f"{r.baseline_mean_dir_acc:.4f}",
            f"{r.baseline_majority_sign_dir_acc:.4f}",
            f"{r.rmse:.4f}", f"{r.baseline_mean_rmse:.4f}",
            "yes" if r.beats_baseline_mean_rmse else "**NO**",
            "yes" if r.beats_both_direction_baselines else "**NO**",
        ])
    lines += _md_table(
        ["asset", "winner", "winner dir. acc.", "baseline_mean dir. acc.",
         "baseline_majority_sign dir. acc.", "winner RMSE", "baseline_mean RMSE",
         "beats mean on RMSE", "beats both direction baselines"], table)
    lines += ["", "### Verdict per asset", ""]
    for r in summary.itertuples():
        if not r.beats_baseline_mean_rmse and not r.beats_both_direction_baselines:
            verdict = "**LOSES to the naive baseline on both RMSE and direction.**"
        elif not r.beats_baseline_mean_rmse:
            verdict = ("Beats both naive direction baselines but **LOSES to "
                       "baseline_mean on RMSE.**")
        elif not r.beats_both_direction_baselines:
            verdict = "Beats baseline_mean on RMSE but **LOSES on direction.**"
        else:
            verdict = "Beats the naive baselines on both RMSE and direction."
        lines.append(f"- `{r.ticker}` ({r.winner}): {verdict}")

    n_lose_rmse = int((~summary["beats_baseline_mean_rmse"]).sum())
    n_lose_dir = int((~summary["beats_both_direction_baselines"]).sum())
    lines += [
        "",
        "## Facts from the Phase 4 run",
        "",
        f"- {n_rmse} of {len(pairs)} model×asset pairs beat `baseline_mean` on RMSE.",
        f"- {n_dir} of {len(pairs)} pairs beat both direction baselines"
        + (f" (all in: {', '.join(dir_winners)})." if dir_winners else "."),
        "- Gold/silver (`GC=F`, `SI=F` — COMEX futures) naive direction accuracy is high "
        "because both drifted upward over 2019–2026; the majority-sign baseline simply "
        "rides that drift.",
        "- No 60–65% accuracy claim is supported by these metrics.",
        "",
        "## Conclusion",
        "",
        f"The selection rule produced five saved models, but {n_lose_rmse} of 5 winners lose "
        f"to the training-mean baseline on RMSE and {n_lose_dir} of 5 do not beat both naive "
        "direction baselines"
        + (f"; only {', '.join(dir_winners)} clears that bar on direction" if dir_winners else "")
        + f". Mean directional accuracy across all 25 model×asset pairs ranges from "
        f"{dir_lo:.3f} to {dir_hi:.3f}, and {r2_note}. The winner is the best of "
        "five scored on the same folds it was picked from, so its scores are optimistic, "
        "and the refit models have no out-of-sample score at all. These files exist so the "
        "pipeline can move forward (Phase 6 needs something to load); they are not evidence "
        "of forecasting skill, and any dashboard copy must say forecasts are experimental "
        "and not advice.",
        "",
        "## Artefacts",
        "",
        "- `artifacts/models/{safe_ticker}_{model}.joblib` — dict with `model`, `model_name`, "
        "`ticker`, `feature_columns`, `train_rows`, `train_end`",
        "- `artifacts/metrics_summary.csv` — the table above",
    ]
    tree = summary[summary["winner"].isin(TREE_MODELS)]
    if len(tree):
        lines.append("- `artifacts/feature_importance.csv` and `artifacts/plots/*_importance.png` "
                     "— tree winners only: "
                     + ", ".join(f"`{t}` ({m})" for t, m in zip(tree["ticker"], tree["winner"])))
    else:
        lines.append("- No tree-model winners, so no feature-importance outputs.")
    (REPORTS_DIR / "phase5_selection.md").write_text("\n".join(lines) + "\n")
