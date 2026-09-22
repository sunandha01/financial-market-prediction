"""Project-wide config: tickers, date range, paths.

Phase 1 only needs the pieces used by data_fetcher / download_data.
Later phases append to this file rather than replacing it.
"""

from pathlib import Path

# Fixed asset universe (see CONTEXT.md). GC=F / SI=F are COMEX futures,
# not MCX spot -- label them as futures anywhere they reach a human.
TICKERS = {
    "INR=X": "USD/INR",
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "GC=F": "Gold futures",
    "SI=F": "Silver futures",
}

START_DATE = "2019-01-01"
END_DATE = None  # None = up to today

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
REPORTS_DIR = BASE_DIR / "reports"
