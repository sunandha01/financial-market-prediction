"""Phase 8: read-only FastAPI over Postgres.

GET routes only SELECT from the database. Admin routes start the existing
jobs (jobs.refresh_prices / jobs.write_forecasts) as separate processes; the
request never trains a model, and this module never calls Yahoo itself.

Run:  uvicorn api.main:app --reload
Docs: http://127.0.0.1:8000/docs
Forecasts are experimental, not investment advice. GC=F / SI=F are COMEX futures.
"""

import hmac
import os
import subprocess
import sys

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from config import ARTIFACTS_DIR, BASE_DIR, TICKERS
from src.db import _load_dotenv, get_connection

_load_dotenv()  # so ADMIN_TOKEN can live in .env next to DATABASE_URL

DISCLAIMER = "Experimental forecast, not investment advice."
HISTORY_MAX_ROWS = 500

app = FastAPI(title="Market prediction API", version="0.8.0")
app.add_middleware(  # localhost only, so Phase 9's dev server can attach
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(psycopg.OperationalError)
async def _db_down(_: Request, exc: psycopg.OperationalError):
    return JSONResponse(status_code=503, content={"detail": "Database unavailable."})


def get_conn():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _rows(conn, sql: str, params=()) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _asset(ticker: str) -> dict:
    """Static asset info; 404 for anything outside the fixed five."""
    if ticker not in TICKERS:
        raise HTTPException(404, f"Unknown ticker {ticker!r}. Known: {list(TICKERS)}")
    futures = ticker.endswith("=F")
    return {
        "ticker": ticker,
        "display_name": f"{TICKERS[ticker]} (COMEX)" if futures else TICKERS[ticker],
        "asset_type": "futures" if futures else "fx",
    }


FORECAST_COLUMNS = ("as_of, pred_return_7d, direction, model_name, last_close, "
                    "beats_baseline_rmse, beats_baseline_direction, created_at")


@app.get("/health")
def health(conn=Depends(get_conn)):
    conn.execute("SELECT 1")
    return {"status": "ok", "database": "ok"}


@app.get("/assets")
def assets(conn=Depends(get_conn)):
    latest = {r["ticker"]: r for r in _rows(
        conn, f"SELECT DISTINCT ON (ticker) ticker, {FORECAST_COLUMNS} "
              "FROM forecasts ORDER BY ticker, as_of DESC")}
    out = []
    for ticker in TICKERS:
        row = dict(latest[ticker]) if ticker in latest else None
        if row:
            row.pop("ticker")
        out.append({**_asset(ticker), "latest_forecast": row})
    return {"disclaimer": DISCLAIMER, "assets": out}


@app.get("/assets/{ticker}/forecast")
def forecast(ticker: str, conn=Depends(get_conn)):
    info = _asset(ticker)
    rows = _rows(conn, f"SELECT {FORECAST_COLUMNS} FROM forecasts WHERE ticker = %s "
                       "ORDER BY as_of DESC LIMIT 1", (ticker,))
    if not rows:
        raise HTTPException(404, f"No forecast stored for {ticker}. Run "
                                 "`python -m jobs.write_forecasts` (or POST /admin/write-forecasts).")
    return {"disclaimer": DISCLAIMER, **info, **rows[0]}


@app.get("/assets/{ticker}/history")
def history(ticker: str, limit: int = HISTORY_MAX_ROWS, conn=Depends(get_conn)):
    info = _asset(ticker)
    limit = max(1, min(limit, HISTORY_MAX_ROWS))  # capped, oldest-first for charts
    rows = _rows(conn, "SELECT date, open, high, low, close, volume FROM ohlcv "
                       "WHERE ticker = %s ORDER BY date DESC LIMIT %s", (ticker, limit))
    rows.reverse()
    return {**info, "count": len(rows), "rows": rows}


@app.get("/assets/{ticker}/metrics")
def metrics(ticker: str, conn=Depends(get_conn)):
    info = _asset(ticker)
    rows = _rows(conn, "SELECT model_name, artifact_path, trained_at, metrics_json AS metrics "
                       "FROM model_runs WHERE ticker = %s ORDER BY trained_at DESC, id DESC LIMIT 1",
                 (ticker,))
    if not rows:
        raise HTTPException(404, f"No model run stored for {ticker}. Run "
                                 "`python -m jobs.record_model_runs`.")
    return {**info, **rows[0],
            "note": "Means over 5 walk-forward folds (Phase 4); the winner was picked on the "
                    "same folds, so these scores are optimistic. Compare with the baseline_* fields."}


@app.get("/status")
def status(conn=Depends(get_conn)):
    return {
        "jobs": _rows(conn, "SELECT DISTINCT ON (job_name) job_name, status, started_at, "
                            "finished_at, message FROM job_runs "
                            "ORDER BY job_name, started_at DESC, id DESC"),
        "forecasts": _rows(conn, "SELECT ticker, max(as_of) AS latest_as_of FROM forecasts "
                                 "GROUP BY ticker ORDER BY ticker"),
        "prices": _rows(conn, "SELECT ticker, max(date) AS latest_date, count(*) AS rows "
                              "FROM ohlcv GROUP BY ticker ORDER BY ticker"),
    }


# --- admin: start existing jobs, never train ---------------------------------

def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(503, "Admin routes are disabled: ADMIN_TOKEN is not set.")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(401, "Missing or invalid X-Admin-Token header.")


_running: dict[str, subprocess.Popen] = {}  # single-process guard against overlapping runs


def _start_job(module: str, *args: str) -> dict:
    running = _running.get(module)
    if running and running.poll() is None:
        raise HTTPException(409, f"{module} is already running.")
    log_dir = ARTIFACTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / f"{module.split('.')[-1]}.log", "ab") as log:
        _running[module] = subprocess.Popen(
            [sys.executable, "-m", module, *args], cwd=BASE_DIR,
            stdout=log, stderr=subprocess.STDOUT)
    return {"started": module, "args": list(args), "check": "GET /status"}


@app.post("/admin/refresh", status_code=202, dependencies=[Depends(require_admin)])
def admin_refresh(force: bool = False):
    """Runs jobs.refresh_prices as a separate process. force=true makes the JOB
    re-download from Yahoo; the request handler itself never calls Yahoo."""
    return _start_job("jobs.refresh_prices", *(["--force"] if force else []))


@app.post("/admin/write-forecasts", status_code=202, dependencies=[Depends(require_admin)])
def admin_write_forecasts():
    return _start_job("jobs.write_forecasts")


@app.post("/admin/retrain", dependencies=[Depends(require_admin)])
def admin_retrain():
    raise HTTPException(501, "Retraining is not available over HTTP in this phase. Run "
                             "scripts/run_pipeline.py and scripts/select_models.py offline.")
