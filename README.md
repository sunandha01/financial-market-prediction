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

## Run — Phase 6 (inference)

Needs the Phase 5 artefacts (`artifacts/models/`, `artifacts/metrics_summary.csv`)
and the `data/` cache. Never downloads, refits or runs CV.

```bash
python -m src.predict GC=F
python -m src.predict GC=F --as-of 2026-06-30
```

Prints one JSON object (ticker, as_of, pred_return_7d, direction,
model_name, model_path, last_close, beats_baseline_rmse,
beats_baseline_direction). `as_of` is the date of the feature row used
(last row on or before `--as-of`). Same inputs give identical output.
`beats_baseline_*` come from `metrics_summary.csv`: today every winner
loses to the mean baseline on RMSE. Forecasts are experimental, not advice;
`--as-of` dates inside the training period are in-sample.

Checks:

```bash
python tests/test_predict.py
```

## Run — Phase 7 (Postgres + jobs)

Needs Postgres running locally (`brew services start postgresql@18`), the
Phase 5 artefacts and the `data/` cache. One-time setup:

```bash
createdb market_predict
cp .env.example .env          # DATABASE_URL, edit if your setup differs
python scripts/migrate.py     # creates ohlcv, forecasts, model_runs, job_runs
```

Jobs (CLI only, safe to re-run, never retrain):

```bash
python -m jobs.refresh_prices            # upsert OHLCV from the data/ cache
python -m jobs.refresh_prices --force    # re-download from Yahoo first
python -m jobs.write_forecasts           # predict() x5 -> forecasts (no Yahoo)
python -m jobs.record_model_runs         # optional: log the Phase 5 winners
```

Check it:

```bash
psql -d market_predict -c "select ticker, as_of, pred_return_7d, direction, model_name from forecasts order by ticker;"
python tests/test_jobs.py                # failure + no-duplicate checks (scratch schema)
```

A failing ticker does not stop the others: the job finishes, writes
`job_runs.status = 'error'` with the failed tickers in `message`, and exits 1.
`.env` is gitignored.

## Run — Phase 8 (FastAPI backend)

Needs the Phase 7 database (migrated and filled by the jobs).

```bash
uvicorn api.main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

```bash
curl localhost:8000/health
curl localhost:8000/assets
curl localhost:8000/assets/GC=F/forecast
curl "localhost:8000/assets/GC=F/history?limit=100"
curl localhost:8000/assets/GC=F/metrics
curl localhost:8000/status
```

Admin routes are disabled until you set `ADMIN_TOKEN` in `.env` (any long
random string), then send it as the `X-Admin-Token` header:

```bash
curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" localhost:8000/admin/write-forecasts
curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" localhost:8000/admin/refresh
```

They start the existing jobs as separate processes (202, then watch
`/status`); `POST /admin/retrain` is a 501 stub and nothing trains over HTTP.
All routes are listed in `reports/phase8_api.md`.

```bash
python tests/test_api.py
```

## Run — Phase 9 (React dashboard)

Needs Node 20.19+ (or 22.12+) and the API running on port 8000 (Phase 8).

```bash
# terminal 1 (project root, venv active)
uvicorn api.main:app --reload
```

```bash
# terminal 2
cd web
npm install
npm run dev
```

Open http://localhost:5173. Pages: Markets (five cards), an asset page per
market (forecast, price chart, model scores), Learn (8 short topics),
Status. The site reads everything from the API; if the API is down it shows
an error, never a number. The API URL defaults to `http://localhost:8000`
(override with `VITE_API_URL`). Type-check and production build:
`npm run build`. Details in `reports/phase9_ui.md`.

## Run — Phase 10 (admin login)

Public pages (Markets, asset pages, Learn, Status) need no login. Only
`/admin` is protected. There is one admin, identified by a secret token.

1. Make a token and put it in your local `.env` (gitignored, never commit it):

   ```bash
   openssl rand -hex 24        # copy the output
   ```

   ```
   ADMIN_TOKEN=paste-it-here
   ```

2. **Stop and restart the API** (Ctrl+C, then `uvicorn api.main:app --reload`).
   `.env` is read once at startup, and `--reload` only watches `.py` files, so
   saving `.env` alone does not update a running server.
3. Open http://localhost:5173/login, paste the token, log in. `/admin` has
   **Refresh prices** and **Write forecasts** (retrain is disabled). **Log out**
   clears the token. Opening `/admin` while logged out sends you to `/login`.

If `ADMIN_TOKEN` is empty the login page says admin routes are disabled.
More detail in `reports/phase10_auth.md`.

```bash
python tests/test_api.py
```

## Out of scope (this phase)

Deployment, HTTPS, user accounts. See `CONTEXT.md`.
