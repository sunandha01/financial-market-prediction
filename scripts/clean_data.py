"""Phase 2 CLI: clean all five cached tickers and print a QA summary.

Usage:
    python scripts/clean_data.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TICKERS, REPORTS_DIR
from src.preprocess import clean


def main():
    results = []
    for ticker in TICKERS:
        try:
            _, qa = clean(ticker)
        except FileNotFoundError as exc:
            print(f"[ERROR] {ticker}: {exc}")
            continue

        results.append(qa)
        print(f"[OK] {ticker} rows {qa['rows_before']} -> {qa['rows_after']} "
              f"(dupes dropped={qa['dropped_duplicates']}, "
              f"missing-OHLC dropped={qa['dropped_missing_ohlc']}) "
              f"{qa['date_min']} -> {qa['date_max']}")
        if qa["gaps"]:
            print(f"  gaps >4 calendar days: {len(qa['gaps'])} (showing up to 5)")
            for start, end, days in qa["gaps"][:5]:
                print(f"    {start} -> {end} ({days} days)")

    _write_report(results)


def _write_report(results):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "phase2_clean.md"
    lines = [
        "# Phase 2 — Cleaning and preprocessing report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Ticker | Rows before | Rows after | Dupes dropped | Missing-OHLC dropped | Start | End | Gaps >4d |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['ticker']} | {r['rows_before']} | {r['rows_after']} | "
            f"{r['dropped_duplicates']} | {r['dropped_missing_ohlc']} | "
            f"{r['date_min']} | {r['date_max']} | {len(r['gaps'])} |"
        )

    lines.append("")
    lines.append("## Gaps longer than 4 calendar days")
    lines.append("(sample only, no prices invented for these dates)")
    any_gaps = False
    for r in results:
        if not r["gaps"]:
            continue
        any_gaps = True
        lines.append(f"\n**{r['ticker']}** — {len(r['gaps'])} gap(s):")
        for start, end, days in r["gaps"][:10]:
            lines.append(f"- {start} -> {end} ({days} days)")
    if not any_gaps:
        lines.append("\nNone found.")

    path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
