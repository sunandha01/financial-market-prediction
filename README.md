# ML-Based Financial Market Prediction System

Phase 1 only (data collection). See `CONTEXT.md` for the full phase plan —
later phases are out of scope until the human says to move on.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python scripts/download_data.py
```

Downloads daily OHLCV for the five fixed tickers (USD/INR, EUR/USD, GBP/USD,
Gold futures, Silver futures) via `yfinance` and caches one CSV per ticker
under `data/`. A second run reuses the cache and does not hit Yahoo again.

Force a fresh download:

```bash
python scripts/download_data.py --force
```

Output: per-ticker row counts, date range, missing-column warnings printed
to the console, plus a summary written to `reports/phase1_data.md`.

## Run — Phase 2 (cleaning)

```bash
python scripts/clean_data.py
```

Reads the cached CSVs from `data/`, drops `Adj Close`, sorts by date,
drops exact duplicate dates and any row missing Open/High/Low/Close, and
prints a QA summary (rows before/after, date range, gaps longer than 4
calendar days). Writes `reports/phase2_clean.md`. Never re-downloads —
run Phase 1's script first if `data/` is empty.

Schema check:

```bash
python tests/test_preprocess.py
```

## Run — Phase 3 (feature engineering + target)

```bash
python scripts/build_features.py
```

Starts from `load_clean(ticker)` (Phase 2) and builds features + the
`target_ret_7d` label via `build_dataset(ticker)`. Prints shape per
ticker and writes `reports/phase3_features.md` (every column name, row
counts before/after warmup+target drop).

Leakage check:

```bash
python tests/test_no_leakage.py
```

## Run — Phase 4 (models + walk-forward validation)

macOS only, once (XGBoost needs the OpenMP runtime):

```bash
brew install libomp
```

```bash
python scripts/run_pipeline.py
```

Scores 5 models x 5 assets with `TimeSeriesSplit(n_splits=5, gap=7)` plus
two naive baselines (training-fold mean return, training-fold majority
sign). Writes `artifacts/metrics_cv.csv` (fold-level), plots under
`artifacts/plots/`, and `reports/phase4_cv.md`. Hyperparameters and the CV
gap live in `config.py`.

## Run — Phase 5 (model selection + artefacts)

Needs `artifacts/metrics_cv.csv` from Phase 4.

```bash
python scripts/select_models.py
```

Picks one winner per asset (highest mean directional accuracy across the
folds among the five ML models; tie -> lower mean RMSE), refits it on all
labelled rows and saves `artifacts/models/{ticker}_{model}.joblib`. Also
writes `artifacts/metrics_summary.csv`, feature importance for tree winners,
and `reports/phase5_selection.md`, which prints each winner next to the
naive baselines. Check the report: most winners do not beat the baselines.

## Out of scope (this phase)

`predict()`, database, API, UI. See `CONTEXT.md`.
