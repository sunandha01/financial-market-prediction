"""Phase 7 job (optional): record the five Phase 5 winners in model_runs.

Re-runnable: rows are unique on (ticker, artifact_path, trained_at), where
trained_at is the model file's modification time, so only a retrain adds a row.

Usage:
    python -m jobs.record_model_runs
"""

import sys
from datetime import datetime, timezone

import pandas as pd
from psycopg.types.json import Jsonb

from config import ARTIFACTS_DIR, BASE_DIR, MODELS_DIR, TICKERS
from src.data_fetcher import _cache_path
from src.db import get_connection, job_run

INSERT = """
INSERT INTO model_runs (ticker, model_name, artifact_path, metrics_json, trained_at)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (ticker, artifact_path, trained_at) DO NOTHING
"""


def run(conn) -> bool:
    with job_run(conn, "record_model_runs") as job:
        summary = pd.read_csv(ARTIFACTS_DIR / "metrics_summary.csv").set_index("ticker")
        added, failed = 0, {}
        for ticker in TICKERS:
            try:
                row = summary.loc[ticker]
                path = MODELS_DIR / f"{_cache_path(ticker).stem}_{row['winner']}.joblib"
                trained_at = datetime.fromtimestamp(int(path.stat().st_mtime), tz=timezone.utc)
                metrics = {k: (v.item() if hasattr(v, "item") else v)
                           for k, v in row.drop("winner").items()}
                with conn.transaction():
                    cur = conn.execute(INSERT, (ticker, row["winner"],
                                                path.relative_to(BASE_DIR).as_posix(),
                                                Jsonb(metrics), trained_at))
                added += cur.rowcount
            except Exception as exc:
                failed[ticker] = str(exc)
                print(f"[ERROR] {ticker}: {exc}")
        job["status"] = "error" if failed else "ok"
        job["message"] = f"inserted {added} new model_runs" + (f"; failed {failed}" if failed else "")
        print(job["message"])
        return not failed


def main() -> None:
    with get_connection() as conn:
        sys.exit(0 if run(conn) else 1)


if __name__ == "__main__":
    main()
