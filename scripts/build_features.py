"""Phase 3 CLI: build the feature+target dataset for all five tickers.

Usage:
    python scripts/build_features.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TICKERS, REPORTS_DIR
from src.preprocess import load_clean
from src.feature_engineering import build_dataset, NON_FEATURE_COLUMNS


def main():
    rows = []
    columns = None
    for ticker in TICKERS:
        clean_rows = len(load_clean(ticker))
        df = build_dataset(ticker)
        print(f"[OK] {ticker} shape={df.shape} "
              f"clean_rows={clean_rows} -> after_warmup_target_drop={len(df)}")
        rows.append({"ticker": ticker, "clean_rows": clean_rows, "final_rows": len(df)})
        if columns is None:
            columns = list(df.columns)

    _write_report(rows, columns)


def _write_report(rows, columns):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "phase3_features.md"
    feature_count = len(columns) - len(NON_FEATURE_COLUMNS) - 1  # - target_ret_7d
    lines = [
        "# Phase 3 — Feature engineering + target report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Total columns: {len(columns)} "
        f"({len(NON_FEATURE_COLUMNS)} passthrough OHLCV/Date + "
        f"{feature_count} features + 1 target)",
        "",
        "## Row counts",
        "",
        "| Ticker | Clean rows (Phase 2) | Rows after warmup/target drop |",
        "|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['ticker']} | {r['clean_rows']} | {r['final_rows']} |")

    lines.append("")
    lines.append("## Columns")
    lines.append("")
    for c in columns:
        lines.append(f"- {c}")

    path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
