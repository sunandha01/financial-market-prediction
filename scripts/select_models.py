"""Phase 5 CLI: pick one winner per asset from the Phase 4 scores and save it.

Needs artifacts/metrics_cv.csv (run scripts/run_pipeline.py first).

Usage:
    python scripts/select_models.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.train_evaluate import select_and_save

if __name__ == "__main__":
    select_and_save()
