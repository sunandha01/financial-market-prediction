"""Phase 7 job: predict() for each ticker and upsert into forecasts.

Never calls Yahoo and never retrains: predict() reads the data/ cache and the
Phase 5 model files. Run jobs.refresh_prices first so ohlcv matches the cache.
Forecasts are experimental, not advice; read the beats_baseline_* columns.

Usage:
    python -m jobs.write_forecasts
"""

import sys
from datetime import date

from config import TICKERS
from src.db import get_connection, job_run
from src.predict import predict

UPSERT = """
INSERT INTO forecasts (ticker, as_of, pred_return_7d, direction, model_name, last_close,
                       beats_baseline_rmse, beats_baseline_direction)
VALUES (%(ticker)s, %(as_of)s, %(pred_return_7d)s, %(direction)s, %(model_name)s,
        %(last_close)s, %(beats_baseline_rmse)s, %(beats_baseline_direction)s)
ON CONFLICT (ticker, as_of) DO UPDATE SET
    pred_return_7d = EXCLUDED.pred_return_7d, direction = EXCLUDED.direction,
    model_name = EXCLUDED.model_name, last_close = EXCLUDED.last_close,
    beats_baseline_rmse = EXCLUDED.beats_baseline_rmse,
    beats_baseline_direction = EXCLUDED.beats_baseline_direction,
    created_at = now()
"""


def run(conn) -> bool:
    """Returns True when every ticker succeeded."""
    with job_run(conn, "write_forecasts") as job:
        done, failed = [], {}
        for ticker in TICKERS:
            try:
                result = predict(ticker)
                params = {**result, "as_of": date.fromisoformat(result["as_of"])}
                with conn.transaction():
                    conn.execute(UPSERT, params)
                done.append(f"{ticker}@{result['as_of']}")
            except Exception as exc:  # keep going; record and move on
                failed[ticker] = str(exc)
                print(f"[ERROR] {ticker}: {exc}")
        job["status"] = "error" if failed else "ok"
        job["message"] = f"wrote {', '.join(done) or 'none'}" + (
            f"; failed {failed}" if failed else "")
        print(job["message"])
        return not failed


def main() -> None:
    with get_connection() as conn:
        sys.exit(0 if run(conn) else 1)


if __name__ == "__main__":
    main()
