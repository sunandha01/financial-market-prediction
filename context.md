# CONTEXT.md — ML-Based Financial Market Prediction System

This is a **major project**. It will take many sessions.

Implement **one phase at a time**. When the phase meets its “Done when” list, stop and wait. Do not start the next phase unless the human says to.

Rules:

1. Read this file. Look at `CURRENT_PHASE`.
2. Do **only** that phase.
3. When finished, say what you built, how to run it, and stop.
4. If the human wants fixes, stay on the same phase.
5. Do not rewrite older phases unless asked.
6. Small working increments. No extra folders for future phases.

---

## CURRENT_PHASE

```
CURRENT_PHASE = 6
PHASE_NAME    = Inference function
STATUS        = built, awaiting review
```

When a phase is finished and the human says to move on, update these three lines.

---

## What this project is

Academic-year **major project** plus a later fullstack product layer.

**One-sentence goal:**
From five years of daily OHLCV, forecast the **7-day forward return** for five markets, using five ML models, evaluated with **walk-forward** validation, then (later) serve forecasts through FastAPI + Postgres + a React dashboard.

**Assets (fixed):**


| Asset   | Yahoo ticker | Notes                                 |
| ------- | ------------ | ------------------------------------- |
| USD/INR | `INR=X`      | FX                                    |
| EUR/USD | `EURUSD=X`   | FX                                    |
| GBP/USD | `GBPUSD=X`   | FX                                    |
| Gold    | `GC=F`       | COMEX gold**futures**, not MCX spot   |
| Silver  | `SI=F`       | COMEX silver**futures**, not MCX spot |

**Target (fixed):**

```text
y[t] = Close[t + 7] / Close[t]  -  1
```

Predict the percentage return seven **trading** days ahead, not the raw price.

**Models (fixed set):**

- Random Forest
- XGBoost
- Ridge (with `StandardScaler`)
- ElasticNet (`l1_ratio=0.5`, with `StandardScaler`)
- sklearn GradientBoostingRegressor

**Validation (non-negotiable):**
`sklearn.model_selection.TimeSeriesSplit` (5 folds). Never shuffle rows. Test window is always after the train window.

**Data source (Phase 1–8):**
Yahoo Finance via `yfinance`. Cache to local CSV. No paid terminals.

This is **not** a live broker, not investment advice, and not a tick-trading engine.

---

## Non-negotiable rules

- Features for day `t` use **only** data at `t` or earlier.
- Do not forward-fill weekends or holidays.
- Do not train on a row that has no 7-day-ahead close.
- Do not call `yf.download` from a web request in later phases.
- Do not train XGBoost inside an HTTP handler.
- Do not put future work (RAG, LSTM, news, broker APIs) into Phases 1–8.
- Label metals as futures in comments, docs, and later UI copy.
- Treat FX volume as indicative / possibly empty — never as true exchange volume.
- Python 3.10+, reproducible `requirements.txt`.
- Code must run on a laptop with no GPU.

---

## Repository layout (create in Phase 1, fill over time)

```text
market-predict/
├── CONTEXT.md                 # this file (keep in repo)
├── README.md                  # how to run the current phase
├── requirements.txt
├── .env.example
├── config.py                  # windows, tickers, paths, model hyperparams
├── data/                      # gitignored raw/cache CSV
│   └── .gitkeep
├── artifacts/                 # gitignored joblib + generated plots
│   └── .gitkeep
├── reports/                   # small markdown notes per closed phase
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py        # Phase 1
│   ├── preprocess.py          # Phase 2
│   ├── feature_engineering.py # Phase 3 (features + target)
│   ├── models.py              # Phase 4
│   ├── train_evaluate.py      # Phase 4–5
│   ├── predict.py             # Phase 6
│   └── visualize.py           # Phase 4–5 plots
├── scripts/
│   ├── download_data.py
│   ├── run_pipeline.py
│   └── write_forecasts.py     # later jobs
├── tests/
│   └── test_no_leakage.py     # start from Phase 3
├── api/                       # Phase 8 only — do not create early
├── web/                       # Phase 9 only — do not create early
└── jobs/                      # Phase 7 only — do not create early
```

Do not scaffold `api/`, `web/`, or `jobs/` before those phases. A fake app tree is noise.

---

## Stack (locked)


| Layer        | Choice                                     |
| ------------ | ------------------------------------------ |
| Language     | Python 3.10+                               |
| Data         | yfinance, pandas, numpy                    |
| Indicators   | `ta` library + pandas where simpler        |
| ML           | scikit-learn, xgboost, joblib              |
| Plots        | matplotlib, seaborn                        |
| Config       | `config.py` + environment variables later  |
| API (later)  | FastAPI                                    |
| DB (later)   | PostgreSQL                                 |
| Web (later)  | React + Tailwind + shadcn, light theme     |
| Jobs (later) | cron or APScheduler calling Python scripts |

Do not switch stack mid-project without an explicit human decision.

Default model settings (from the project report — change only after a review):

```text
RandomForest: n_estimators=300, max_depth=10, min_samples_split=5, min_samples_leaf=2
XGBoost:      n_estimators=300, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8
Horizon:      7 trading days
History:      ~5 years daily bars (start 2019-01-01 unless config says otherwise)
CV:           TimeSeriesSplit n_splits=5
```

---

## Phase plan (major project)

Do these **in order**. Each phase has a definition of done. The human reviews before the next phase starts.

### Phase 1 — Data collection  ← YOU ARE HERE

**Goal:** Reliable local cache of daily OHLCV for the five tickers.

**Build:**

- `config.py` with tickers, date range, paths
- `src/data_fetcher.py`
- `scripts/download_data.py`
- `data/` cache
- `requirements.txt` (yfinance, pandas, numpy)
- `README.md` with run instructions for this phase only

**Behaviour:**

- Download each ticker with `yfinance`
- Flatten multi-level columns
- Save one CSV per ticker under `data/`
- Skip download if cache exists and `--force` was not passed
- Print row counts, date min/max, and missing-column warnings
- Do not crash the whole run if one ticker fails; record the error and continue

**Done when:**

- `python scripts/download_data.py` produces five readable CSVs
- Second run does not hit Yahoo unless `--force`
- README says exactly how to run it
- A short `reports/phase1_data.md` lists ticker, rows, start, end

**Out of scope:** cleaning logic beyond flattening headers, features, models, API.

---

### Phase 2 — Cleaning and preprocessing

**Goal:** One tidy frame per asset that later phases can trust.

**Build:** `src/preprocess.py` + tests for column names.

**Rules:**

- Canonical columns: `Date, Open, High, Low, Close, Volume` (Date as index or column, but one convention only)
- Sort by date ascending
- Drop exact duplicate dates
- Do **not** forward-fill missing sessions
- Volume may be NaN for FX — keep the column
- Reject rows with missing OHLC
- Optional QA print: gaps longer than 4 calendar days

**Done when:**

- A function `load_clean(ticker) -> DataFrame` works for all five files
- Column schema is identical across assets
- `reports/phase2_clean.md` notes row loss vs raw cache

**Out of scope:** indicators, target, models.

---

### Phase 3 — Feature engineering + target

**Goal:** Supervised table: 50+ features + `target_ret_7d`.

**Build:** `src/feature_engineering.py` and `tests/test_no_leakage.py`.

**Feature groups (must implement):**

- Momentum: RSI(14), MACD(12/26/9) + signal + hist, ret_1 / ret_5 / ret_21, log_ret_1
- Trend: SMA 5/10/20/50 and price−SMA, EMA 9/21 and EMA9−EMA21
- Volatility: Bollinger 20,2 (upper, lower, bandwidth, percent-b), ATR(14), roll_std 5 and 21
- Lags of close and of 1-day return at 1,2,3,5,7,14,21
- Calendar: dayofweek, month, quarter

**Target:** `Close.shift(-7) / Close - 1`
Drop rows where target is NaN.
Drop rows where indicator warmup is NaN.

**Leakage test (required):**
A unit test that fails if any feature column at index `t` is computed from close after `t` (spot-check: target uses `shift(-7)`; features use only `shift(positive)` or rolling windows that end at `t`).

**Done when:**

- `build_dataset(ticker)` returns X-ready frame with `target_ret_7d`
- Shape printed per asset
- Leakage test passes
- `reports/phase3_features.md` lists every column name

**Out of scope:** fitting models.

---

### Phase 4 — Models + walk-forward validation

**Goal:** Fair scores for 5 models × 5 assets.

**Build:** `src/models.py`, `src/train_evaluate.py`, `src/visualize.py` (basic).

**Must:**

- `TimeSeriesSplit(n_splits=5)`
- Metrics: MAE, RMSE, R², MAPE, directional accuracy
  Directional accuracy = mean(sign(y_hat) == sign(y_true)) excluding exact zeros if needed
- Also report a **naive baseline** on the same folds: predict the training-set mean return (regression) and the training-set majority sign (direction)
- Save fold-level metrics to `artifacts/metrics_cv.csv`
- One plot per asset: predicted vs actual on the last fold (optional if time is short; required before phase close)

**Done when:**

- One command trains all pairs and writes `artifacts/metrics_cv.csv`
- Baseline columns exist so later review can see whether trees beat the mean
- Runtime stays laptop-reasonable (defaults in config; reduce `n_estimators` only via config if too slow, and document it)

**Out of scope:** picking a production winner file, API.

---

### Phase 5 — Model selection + artefacts

**Goal:** One saved model per asset + a comparison table.

**Build:** selection rule in `train_evaluate.py`, joblib dumps, `reports/phase5_selection.md`.

**Selection rule (default):**
Highest mean directional accuracy across folds; if tie, lower mean RMSE.
Document the rule in code comments. Do not silently change it.

**Write:**

- `artifacts/models/{ticker}_{model}.joblib`
- `artifacts/metrics_summary.csv`
- Feature importance for tree winners (CSV + bar plot)

**Done when:**

- Five joblib files load with `joblib.load`
- Summary names the winner per ticker and why

---

### Phase 6 — Inference function

**Goal:** Pure function used later by jobs and API.

**Build:** `src/predict.py`

```text
predict(ticker, as_of=None) -> dict
```

Returns at least:

```json
{
  "ticker": "GC=F",
  "as_of": "YYYY-MM-DD",
  "pred_return_7d": -0.012,
  "direction": "down",
  "model_name": "xgboost",
  "model_path": "artifacts/models/...",
  "last_close": 1234.5
}
```

Rules:

- Uses latest complete feature row at or before `as_of`
- Does not download market data if cache is present
- Deterministic: same inputs → same dict
- CLI: `python -m src.predict GC=F`

**Done when:** two CLI runs in a row print the same JSON.

---

### Phase 7 — Database + nightly jobs

**Goal:** Postgres is the source of truth for prices and forecasts.

**Tables (minimum):**

- `ohlcv(ticker, date, open, high, low, close, volume)`
- `forecasts(ticker, as_of, pred_return_7d, direction, model_name, created_at)`
- `model_runs(id, ticker, model_name, artifact_path, metrics_json, trained_at)`
- `job_runs(id, job_name, started_at, finished_at, status, message)`

**Jobs:**

- `jobs/refresh_prices.py` — fetch + upsert OHLCV
- `jobs/write_forecasts.py` — features + `predict()` + upsert forecast

No FastAPI yet. Run jobs from CLI.

**Done when:** after a job, SQL shows new rows and a failed Yahoo pull writes `job_runs.status='error'` without killing the machine.

---

### Phase 8 — FastAPI backend

**Goal:** Read-only HTTP over the database. Admin routes queue jobs; they do not train inline.

**Routes (minimum):**

- `GET /health`
- `GET /assets`
- `GET /assets/{ticker}/forecast`
- `GET /assets/{ticker}/history`
- `GET /assets/{ticker}/metrics`
- `GET /status`
- `POST /admin/refresh` (protected stub ok)
- `POST /admin/retrain` (protected stub — queue only)

**Done when:** frontend-less `curl` returns the same forecast as `src.predict`.

---

### Phase 9 — React dashboard

**Goal:** Light, mobile-first UI. Five asset cards + one detail page + status + disclaimer.

Must show `as_of`, model name, predicted %, direction.
Must label `GC=F` / `SI=F` as futures.
Must say forecasts are experimental, not advice.

No auth required yet unless deploying publicly in this phase.

**Done when:** UI reads live API data; no hardcoded predictions.

---

### Phase 10 — Authentication + user features

Login, protect admin, optional saved watch list.
Do not add social or billing.

---

### Phase 11 — Deployment

One VPS or equivalent: API + jobs + static frontend, env files, Nginx, backups of Postgres, log rotation.
Yahoo failures must surface on `/status`, not take the site down.

---

### Phase 12 — Research / advanced (optional, one item at a time)

Only after Phase 9 works. Pick **one** per cycle:

- Macro features (DXY, VIX, crude)
- News sentiment **as a numeric column** (not a chatbot)
- Paper PnL with a simple spread assumption
- Docs/explain RAG over this repo + forecast JSON
- Extra horizons (1d, 30d)
- LSTM comparison

Live broker execution is a **different project**. Do not sneak it in.

---

## How Claude should start and end a session

Start by stating the phase number and that later phases are off limits.

End with:

- files created or changed
- exact run command
- anything broken or unfinished in **this** phase

Then stop. The human will look at it, ask for changes, or say to start the next phase.

---

## What “good” looks like for a major project

- Another student can clone, create a venv, and reproduce Phase-N outputs from the README
- Leakage test exists from Phase 3 onward
- Metrics include a naive baseline from Phase 4 onward
- Forecasts carry `as_of` and model name from Phase 6 onward
- Public copy never claims guaranteed profit

Accuracy may be modest. That is acceptable. Fake accuracy is not.

---

## First command for Phase 1

When this file is handed to Claude and `CURRENT_PHASE = 1`, Claude should:

1. Create the repo tree listed above (only folders needed for Phase 1).
2. Write `config.py`, `src/data_fetcher.py`, `scripts/download_data.py`, `requirements.txt`, `README.md`.
3. Run the downloader if the environment has network access; if not, still write the code and document the command.
4. Stop. Do not start preprocessing.

---

## Project name and copy

- Title: **ML-Based Financial Market Prediction System**
- Subtitle: Predicting Forex and Precious Metal Prices Using Machine Learning
- Context: Department of Computer Science / Data Science, Academic Year 2024–2025 (major project; implementation may extend)

Keep comments and README professional. No hype about 60–65% accuracy unless that number is sitting in `artifacts/metrics_summary.csv` from Phase 5.
