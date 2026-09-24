# Phase 8 — FastAPI backend report

Run: `uvicorn api.main:app --reload` (docs at `/docs`). Read-only over the Phase 7 Postgres database (`market_predict`); no route trains a model or calls Yahoo. CORS allows `http://localhost:*` / `127.0.0.1:*` only. Forecasts are experimental, not investment advice; `GC=F` / `SI=F` are COMEX futures.

`predict()` (Phase 6) still reads the CSV cache; the API reads the `forecasts` table written by `jobs.write_forecasts`. The gold value from `GET /assets/GC=F/forecast` is **-0.00022384291008135308**, identical to `python -m src.predict GC=F`.

## Routes

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | – | liveness + database check (503 if the DB is down) |
| GET | `/assets` | – | the 5 assets with `display_name`, `asset_type` (`fx`/`futures`), latest forecast (or `null`) and a `disclaimer` |
| GET | `/assets/{ticker}/forecast` | – | latest `forecasts` row; 404 with a hint if none stored |
| GET | `/assets/{ticker}/history?limit=N` | – | last N `ohlcv` rows, oldest first; N capped at 500 (default 500) |
| GET | `/assets/{ticker}/metrics` | – | latest `model_runs` row: winner, CV metrics and the naive baselines |
| GET | `/status` | – | last `job_runs` row per job, latest forecast `as_of` and latest price date per ticker |
| POST | `/admin/refresh[?force=true]` | `X-Admin-Token` | starts `jobs.refresh_prices` as a separate process (202). `force=true` makes the *job* re-download; the handler never calls Yahoo |
| POST | `/admin/write-forecasts` | `X-Admin-Token` | starts `jobs.write_forecasts` (202) |
| POST | `/admin/retrain` | `X-Admin-Token` | stub, always 501 |

Admin routes: 503 if `ADMIN_TOKEN` is not set, 401 if the header is missing or wrong, 409 if that job is already running. Job output goes to `artifacts/logs/`. Unknown ticker: 404.

## Sample curls (real output, shortened)

```bash
curl localhost:8000/health
# {"status":"ok","database":"ok"}

curl localhost:8000/assets
# {"disclaimer":"Experimental forecast, not investment advice.","assets":[
#   {"ticker":"INR=X","display_name":"USD/INR","asset_type":"fx","latest_forecast":{"as_of":"2026-09-22","pred_return_7d":0.001695136261097704,...}},
#   ...
#   {"ticker":"GC=F","display_name":"Gold futures (COMEX)","asset_type":"futures","latest_forecast":{"as_of":"2026-09-22","pred_return_7d":-0.00022384291008135308,...}},
#   {"ticker":"SI=F","display_name":"Silver futures (COMEX)","asset_type":"futures",...}]}

curl localhost:8000/assets/GC=F/forecast
# {"disclaimer":"Experimental forecast, not investment advice.","ticker":"GC=F",
#  "display_name":"Gold futures (COMEX)","asset_type":"futures","as_of":"2026-09-22",
#  "pred_return_7d":-0.00022384291008135308,"direction":"down","model_name":"gradient_boosting",
#  "last_close":4363.39990234375,"beats_baseline_rmse":false,"beats_baseline_direction":false,
#  "created_at":"2026-09-24T20:09:36.249930+05:30"}

curl "localhost:8000/assets/GC=F/history?limit=2"
# {"ticker":"GC=F",...,"count":2,"rows":[
#   {"date":"2026-09-21","open":4413.0,"high":4422.10009765625,"low":4360.2998046875,"close":4383.89990234375,"volume":142919.0},
#   {"date":"2026-09-22","open":4382.5,"high":4414.10009765625,"low":4327.60009765625,"close":4363.39990234375,"volume":121185.0}]}

curl localhost:8000/assets/GC=F/metrics
# {"ticker":"GC=F",...,"model_name":"gradient_boosting","artifact_path":"artifacts/models/GC_F_gradient_boosting.joblib",
#  "trained_at":"2026-09-23T21:43:32+05:30","metrics":{"dir_acc":0.5484,"rmse":0.0361,"baseline_mean_dir_acc":0.5720,
#  "baseline_mean_rmse":0.0288,"beats_baseline_mean_rmse":false,"beats_both_direction_baselines":false,...},"note":"..."}

curl localhost:8000/status
# {"jobs":[{"job_name":"refresh_prices","status":"ok",...},{"job_name":"write_forecasts","status":"ok",...},...],
#  "forecasts":[{"ticker":"EURUSD=X","latest_as_of":"2026-09-22"},...],
#  "prices":[{"ticker":"EURUSD=X","latest_date":"2026-09-22","rows":2010},...]}

curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" localhost:8000/admin/refresh
# {"started":"jobs.refresh_prices","args":[],"check":"GET /status"}          (202)

curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" localhost:8000/admin/write-forecasts
# {"started":"jobs.write_forecasts","args":[],"check":"GET /status"}         (202)

curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" localhost:8000/admin/retrain
# {"detail":"Retraining is not available over HTTP in this phase. Run scripts/run_pipeline.py and scripts/select_models.py offline."}   (501)
```

## Verified

- All five tickers: API forecast equals `predict()` exactly (value, `as_of`, direction, model, last close, both `beats_*` flags) — `tests/test_api.py`.
- Admin jobs run through `/admin/*` left `ohlcv` at 9917 rows and `forecasts` at 5 (no duplicates).
- Empty `forecasts` table → 404 with a message pointing at `jobs.write_forecasts` (tested in a throwaway schema); no Yahoo call.
- History `limit=99999` returns 500 rows; unknown ticker → 404; admin without a token → 401; CORS header only for localhost origins.
