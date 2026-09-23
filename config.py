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

# --- Phase 4: models + walk-forward validation ---
RANDOM_STATE = 42
CV_SPLITS = 5
# Purge 7 rows (= feature_engineering.HORIZON) between train and test: the last
# train rows' targets look 7 days ahead and would otherwise overlap the test
# window. Set to 0 for a plain TimeSeriesSplit(n_splits=5).
CV_GAP = 7

RF_PARAMS = dict(n_estimators=300, max_depth=10, min_samples_split=5,
                 min_samples_leaf=2, n_jobs=-1, random_state=RANDOM_STATE)
XGB_PARAMS = dict(n_estimators=300, learning_rate=0.05, max_depth=6,
                  subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
                  random_state=RANDOM_STATE)
RIDGE_PARAMS = dict(alpha=1.0)
# Returns are ~1e-2 in scale; sklearn's default alpha=1.0 would shrink every
# ElasticNet coefficient to zero (a constant predictor), so use a small alpha.
ELASTICNET_PARAMS = dict(alpha=0.001, l1_ratio=0.5, max_iter=10000,
                         random_state=RANDOM_STATE)
GBR_PARAMS = dict(n_estimators=200, learning_rate=0.05, max_depth=3,
                  subsample=0.8, random_state=RANDOM_STATE)

PLOTS_DIR = ARTIFACTS_DIR / "plots"
