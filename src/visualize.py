"""Phase 4: predicted-vs-actual plots for the last CV fold (one PNG per asset)."""

import matplotlib

matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import pandas as pd

from config import PLOTS_DIR


def plot_last_fold(ticker: str, preds: pd.DataFrame) -> None:
    """preds: Date, actual, then one column per model (and baseline_mean)."""
    model_cols = [c for c in preds.columns if c not in ("Date", "actual")]
    fig, axes = plt.subplots(len(model_cols), 1, figsize=(10, 2.2 * len(model_cols)),
                             sharex=True)
    for ax, col in zip(axes, model_cols):
        ax.plot(preds["Date"], preds["actual"], color="0.6", lw=1, label="actual")
        ax.plot(preds["Date"], preds[col], lw=1, label=col)
        ax.axhline(0, color="0.85", lw=0.5)
        ax.set_ylabel(col, fontsize=8)
    axes[0].legend(loc="upper right", fontsize=7)
    axes[0].set_title(f"{ticker} — 7-day return, last CV fold (predicted vs actual)")
    fig.tight_layout()
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS_DIR / f"{ticker.replace('=', '_')}_last_fold.png", dpi=110)
    plt.close(fig)


def plot_importance(ticker: str, model_name: str, importance: pd.DataFrame, top: int = 15) -> None:
    """importance: feature, importance columns, sorted descending (tree winners only)."""
    top_rows = importance.head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(top_rows) + 1.2))
    ax.barh(top_rows["feature"], top_rows["importance"])
    ax.set_title(f"{ticker} — {model_name} feature importance (top {len(top_rows)})")
    fig.tight_layout()
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS_DIR / f"{ticker.replace('=', '_')}_{model_name}_importance.png", dpi=110)
    plt.close(fig)
