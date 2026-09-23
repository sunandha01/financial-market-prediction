"""Phase 3: feature engineering + target.

build_dataset(ticker) starts from src.preprocess.load_clean(ticker) --
never re-reads raw CSVs with a second schema.

Leakage rule: every feature at row t uses only data at t or earlier
(shift(positive), pct_change, or a rolling/ewm window ending at t). The
ONLY negative-shift line anywhere in this module builds the target
(HORIZON days forward) in build_dataset -- tests/test_no_leakage.py
enforces that this stays true.
"""

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange, BollingerBands

from src.preprocess import load_clean

HORIZON = 7
LAG_STEPS = [1, 2, 3, 5, 7, 14, 21]
NON_FEATURE_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def _add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Every column added here uses shift(positive) or a rolling/ewm
    window ending at the current row -- no negative shift, ever."""
    out = df.copy()
    close, high, low = out["Close"], out["High"], out["Low"]

    # --- Momentum ---
    out["rsi_14"] = RSIIndicator(close, window=14).rsi()
    macd = MACD(close, window_slow=26, window_fast=12, window_sign=9)
    out["macd"] = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"] = macd.macd_diff()
    out["ret_1"] = close.pct_change(1)
    out["ret_5"] = close.pct_change(5)
    out["ret_21"] = close.pct_change(21)
    out["log_ret_1"] = np.log(close / close.shift(1))

    # --- Trend ---
    for w in (5, 10, 20, 50):
        sma = close.rolling(w).mean()
        out[f"sma_{w}"] = sma
        out[f"close_minus_sma_{w}"] = close - sma
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    out["ema_9"] = ema9
    out["ema_21"] = ema21
    out["ema9_minus_ema21"] = ema9 - ema21

    # --- Volatility ---
    bb = BollingerBands(close, window=20, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_lower"] = bb.bollinger_lband()
    out["bb_bandwidth"] = bb.bollinger_wband()
    out["bb_percent_b"] = bb.bollinger_pband()
    out["atr_14"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    out["roll_std_5"] = out["ret_1"].rolling(5).std()
    out["roll_std_21"] = out["ret_1"].rolling(21).std()

    # --- Lags ---
    for k in LAG_STEPS:
        out[f"close_lag_{k}"] = close.shift(k)
        out[f"ret1_lag_{k}"] = out["ret_1"].shift(k)

    # --- Calendar ---
    out["dayofweek"] = out["Date"].dt.dayofweek
    out["month"] = out["Date"].dt.month
    out["quarter"] = out["Date"].dt.quarter

    return out


def build_dataset(ticker: str) -> pd.DataFrame:
    """load_clean(ticker) -> features -> target_ret_7d.

    Drops rows where the target is NaN (last HORIZON sessions) and rows
    where any indicator is still in its warmup window.
    """
    df = load_clean(ticker)
    df = _add_features(df)

    # The only negative shift in this module -- target looks forward,
    # features never do.
    df["target_ret_7d"] = df["Close"].shift(-HORIZON) / df["Close"] - 1

    df = df.dropna().reset_index(drop=True)
    return df
