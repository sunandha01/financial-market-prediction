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

## Out of scope (this phase)

Models, walk-forward validation, API. See `CONTEXT.md`.
