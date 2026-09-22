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

## Out of scope (this phase)

Cleaning beyond flattening yfinance's column headers, feature engineering,
models, API. See `CONTEXT.md`.
