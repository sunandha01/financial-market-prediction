"""Phase 7: Postgres connection + job_runs bookkeeping.

DATABASE_URL comes from the environment (or a local .env, see .env.example).
Connections are autocommit; data writes use explicit transactions so a failed
ticker rolls back alone and the job_runs row is never lost with it.
"""

import os
from contextlib import contextmanager

import psycopg

from config import BASE_DIR


def _load_dotenv() -> None:
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def get_connection() -> psycopg.Connection:
    _load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set -- copy .env.example to .env")
    return psycopg.connect(url, autocommit=True)


@contextmanager
def job_run(conn: psycopg.Connection, job_name: str):
    """Record a job in job_runs. The body sets job['status'] ('ok'|'error') and
    job['message']; an unexpected exception is logged as 'error' and re-raised."""
    job_id = conn.execute(
        "INSERT INTO job_runs (job_name, status) VALUES (%s, 'running') RETURNING id",
        (job_name,),
    ).fetchone()[0]
    job = {"status": "ok", "message": ""}
    try:
        yield job
    except Exception as exc:
        job["status"], job["message"] = "error", f"unexpected: {exc!r}"
        raise
    finally:
        conn.execute(
            "UPDATE job_runs SET finished_at = now(), status = %s, message = %s WHERE id = %s",
            (job["status"], job["message"], job_id),
        )
