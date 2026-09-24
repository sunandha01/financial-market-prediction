"""Phase 7 job: upsert OHLCV from the data/ cache into Postgres.

Reuses src/data_fetcher.fetch_ticker (cache hit = no Yahoo call; a missing
cache or --force downloads) and src/preprocess.load_clean. One ticker failing
never stops the others; any failure marks the job_runs row 'error'.

Usage:
    python -m jobs.refresh_prices            # from cache
    python -m jobs.refresh_prices --force    # re-download from Yahoo first
"""

import argparse
import sys

import pandas as pd

from config import TICKERS
from src.data_fetcher import fetch_ticker
from src.db import get_connection, job_run
from src.preprocess import load_clean

UPSERT = """
INSERT INTO ohlcv (ticker, date, open, high, low, close, volume)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (ticker, date) DO UPDATE SET
    open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
    close = EXCLUDED.close, volume = EXCLUDED.volume
"""


def _rows(ticker: str, df: pd.DataFrame) -> list[tuple]:
    return [
        (ticker, d.date(), float(o), float(h), float(l), float(c),
         None if pd.isna(v) else float(v))
        for d, o, h, l, c, v in df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        .itertuples(index=False)
    ]


def run(conn, force: bool = False) -> bool:
    """Returns True when every ticker succeeded."""
    with job_run(conn, "refresh_prices") as job:
        done, failed = [], {}
        for ticker in TICKERS:
            try:
                res = fetch_ticker(ticker, force=force)
                if res["error"] and not res["rows"]:  # error with rows = recovered cache
                    raise RuntimeError(res["error"])
                rows = _rows(ticker, load_clean(ticker))
                with conn.transaction(), conn.cursor() as cur:
                    cur.executemany(UPSERT, rows)
                done.append(f"{ticker}:{len(rows)}")
            except Exception as exc:  # keep going; record and move on
                failed[ticker] = str(exc)
                print(f"[ERROR] {ticker}: {exc}")
        job["status"] = "error" if failed else "ok"
        job["message"] = f"upserted {', '.join(done) or 'none'}" + (
            f"; failed {failed}" if failed else "")
        print(job["message"])
        return not failed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="re-download from Yahoo first")
    args = parser.parse_args()
    with get_connection() as conn:
        sys.exit(0 if run(conn, force=args.force) else 1)


if __name__ == "__main__":
    main()
