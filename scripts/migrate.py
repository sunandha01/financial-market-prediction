"""Phase 7: create the tables from schema.sql (safe to re-run).

Usage:
    python scripts/migrate.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BASE_DIR
from src.db import get_connection

if __name__ == "__main__":
    with get_connection() as conn:
        conn.execute((BASE_DIR / "schema.sql").read_text())
    print("Schema applied (ohlcv, forecasts, model_runs, job_runs).")
