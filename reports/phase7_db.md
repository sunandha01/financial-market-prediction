# Phase 7 — Database + nightly jobs report

Generated: 2026-09-24T20:10:25

**Database: PostgreSQL 18 (Homebrew, already running locally), database `market_predict`.** No SQLite was used. Connection string comes from `DATABASE_URL` (see `.env.example`; `.env` is gitignored).

## Tables (`schema.sql`, applied by `scripts/migrate.py`, safe to re-run)

| Table | Primary key | Purpose |
|---|---|---|
| `ohlcv` | (ticker, date) | daily OHLCV mirror of the `data/` cache (Phase 2 clean schema). Metals are COMEX futures, not MCX spot; FX volume is indicative only |
| `forecasts` | (ticker, as_of) | one row per ticker per feature date: pred_return_7d, direction, model_name, last_close, beats_baseline_rmse, beats_baseline_direction, created_at |
| `model_runs` | id, UNIQUE (ticker, artifact_path, trained_at) | the Phase 5 winners with their CV metrics as JSON |
| `job_runs` | id | one row per job execution: started_at, finished_at, status (running/ok/error), message |

## Commands

```bash
createdb market_predict
cp .env.example .env
python scripts/migrate.py
python -m jobs.refresh_prices            # or --force to re-download
python -m jobs.write_forecasts
python -m jobs.record_model_runs         # optional
```

Jobs call existing Python (`fetch_ticker`, `load_clean`, `predict`); they never retrain. `write_forecasts` never calls Yahoo. Note that `predict()` reads the CSV cache, not the `ohlcv` table, so run `refresh_prices` first to keep the two aligned.

## Sample SELECT (real output)

```sql
select ticker, as_of, round(pred_return_7d::numeric,5) as pred_return_7d, direction, model_name,
       last_close::numeric(12,4), beats_baseline_rmse, beats_baseline_direction
from forecasts order by ticker;
```

```
  ticker  |   as_of    | pred_return_7d | direction |    model_name     | last_close | beats_baseline_rmse | beats_baseline_direction 
----------+------------+----------------+-----------+-------------------+------------+---------------------+--------------------------
 EURUSD=X | 2026-09-22 |        0.00127 | up        | ridge             |     1.1452 | f                   | f
 GBPUSD=X | 2026-09-22 |       -0.00056 | down      | elasticnet        |     1.3356 | f                   | t
 GC=F     | 2026-09-22 |       -0.00022 | down      | gradient_boosting |  4363.3999 | f                   | f
 INR=X    | 2026-09-22 |        0.00170 | up        | elasticnet        |    95.5800 | f                   | f
 SI=F     | 2026-09-22 |        0.00626 | up        | ridge             |    66.1700 | f                   | f
(5 rows)
```

The GC=F value matches `python -m src.predict GC=F` (-0.000224). Every winner has `beats_baseline_rmse = f`; only GBPUSD=X beats both direction baselines. Forecasts are experimental, not advice.

## Idempotency (both jobs run twice)

Row counts after the second run (identical to after the first; 0 duplicate (ticker, date) pairs):

```
     t      | count 
------------+-------
 ohlcv      |  9917
 forecasts  |     5
 model_runs |     5
(3 rows)
```

Only `job_runs` grows, by design (it is the audit log):

```
 id |     job_name      | status |                           message                            
----+-------------------+--------+--------------------------------------------------------------
  1 | refresh_prices    | ok     | upserted INR=X:2010, EURUSD=X:2010, GBPUSD=X:2010, GC=F:1944
  2 | write_forecasts   | ok     | wrote INR=X@2026-09-22, EURUSD=X@2026-09-22, GBPUSD=X@2026-0
  3 | record_model_runs | ok     | inserted 5 new model_runs
  4 | refresh_prices    | ok     | upserted INR=X:2010, EURUSD=X:2010, GBPUSD=X:2010, GC=F:1944
  5 | write_forecasts   | ok     | wrote INR=X@2026-09-22, EURUSD=X@2026-09-22, GBPUSD=X@2026-0
  6 | record_model_runs | ok     | inserted 0 new model_runs
(6 rows)
```

## Failure handling

`tests/test_jobs.py` (throwaway schema, real tables untouched) simulates a Yahoo failure for GC=F: the other four tickers still load, `job_runs.status = 'error'` with GC=F named in `message`, the job returns non-zero, and the next run recovers and fills GC=F. Re-running both jobs adds no duplicate rows.
