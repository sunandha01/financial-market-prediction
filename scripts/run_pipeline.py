"""Phase 4 CLI: walk-forward CV of all 5 models on all 5 assets.

Usage:
    python scripts/run_pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.train_evaluate import run_all

if __name__ == "__main__":
    run_all()
