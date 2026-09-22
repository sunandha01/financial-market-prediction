"""Phase 1 CLI: download/cache OHLCV for the fixed ticker list.

Usage:
    python scripts/download_data.py           # use cache if present
    python scripts/download_data.py --force   # re-download everything
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TICKERS, REPORTS_DIR
from src.data_fetcher import fetch_ticker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                         help="ignore cache and re-download all tickers")
    args = parser.parse_args()

    rows = []
    for ticker, label in TICKERS.items():
        res = fetch_ticker(ticker, force=args.force)
        rows.append(res)

        if res["error"]:
            print(f"[ERROR] {ticker} ({label}): {res['error']}")
            continue

        source = "cache" if res["cached"] else "downloaded"
        print(f"[OK] {ticker} ({label}) [{source}] rows={res['rows']} "
              f"{res['start']} -> {res['end']}")
        if res["missing_columns"]:
            print(f"  [WARN] missing columns: {res['missing_columns']}")

    _write_report(rows)


def _write_report(rows):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "phase1_data.md"
    lines = [
        "# Phase 1 — Data collection report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Ticker | Rows | Start | End | Status |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        status = r["error"] if r["error"] else "ok"
        lines.append(f"| {r['ticker']} | {r['rows']} | {r['start']} | "
                      f"{r['end']} | {status} |")
    path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
