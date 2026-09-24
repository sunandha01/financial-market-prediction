"""Phase 7 checks against a throwaway Postgres schema (real tables untouched).
No pytest -- run directly:

    python tests/test_jobs.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BASE_DIR
from jobs import refresh_prices, write_forecasts
from src.data_fetcher import fetch_ticker as real_fetch
from src.db import get_connection

SCRATCH = "phase7_test_scratch"


def _count(conn, sql):
    return conn.execute(sql).fetchone()[0]


def test_failed_ticker_is_recorded_and_others_continue(conn):
    def flaky_fetch(ticker, force=False):
        if ticker == "GC=F":
            return {"ticker": ticker, "rows": 0, "error": "simulated Yahoo failure"}
        return real_fetch(ticker, force=False)  # cache only, never hits Yahoo

    original, refresh_prices.fetch_ticker = refresh_prices.fetch_ticker, flaky_fetch
    try:
        assert refresh_prices.run(conn) is False
    finally:
        refresh_prices.fetch_ticker = original

    status, message = conn.execute(
        "SELECT status, message FROM job_runs WHERE job_name='refresh_prices'").fetchone()
    assert status == "error" and "GC=F" in message, (status, message)
    assert _count(conn, "SELECT count(DISTINCT ticker) FROM ohlcv") == 4
    assert _count(conn, "SELECT count(*) FROM ohlcv WHERE ticker='GC=F'") == 0


def test_second_run_creates_no_duplicates(conn):
    assert refresh_prices.run(conn) is True  # GC=F recovers on the next run
    n_ohlcv = _count(conn, "SELECT count(*) FROM ohlcv")
    assert write_forecasts.run(conn) is True
    assert refresh_prices.run(conn) is True and write_forecasts.run(conn) is True
    assert _count(conn, "SELECT count(*) FROM ohlcv") == n_ohlcv
    assert _count(conn, "SELECT count(*) FROM forecasts") == 5


if __name__ == "__main__":
    conn = get_connection()
    try:
        conn.execute(f"DROP SCHEMA IF EXISTS {SCRATCH} CASCADE")
        conn.execute(f"CREATE SCHEMA {SCRATCH}")
        conn.execute(f"SET search_path TO {SCRATCH}")
        conn.execute((BASE_DIR / "schema.sql").read_text())
        test_failed_ticker_is_recorded_and_others_continue(conn)
        test_second_run_creates_no_duplicates(conn)
        print("All Phase 7 job checks passed.")
    finally:
        conn.execute("SET search_path TO public")
        conn.execute(f"DROP SCHEMA IF EXISTS {SCRATCH} CASCADE")
        conn.close()
