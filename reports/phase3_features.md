# Phase 3 — Feature engineering + target report

Generated: 2026-09-23T21:03:03

Total columns: 50 (6 passthrough OHLCV/Date + 43 features + 1 target)

## Row counts

| Ticker | Clean rows (Phase 2) | Rows after warmup/target drop |
|---|---|---|
| INR=X | 2010 | 1954 |
| EURUSD=X | 2010 | 1954 |
| GBPUSD=X | 2010 | 1954 |
| GC=F | 1944 | 1888 |
| SI=F | 1943 | 1887 |

## Columns

- Date
- Open
- High
- Low
- Close
- Volume
- rsi_14
- macd
- macd_signal
- macd_hist
- ret_1
- ret_5
- ret_21
- log_ret_1
- sma_5
- close_minus_sma_5
- sma_10
- close_minus_sma_10
- sma_20
- close_minus_sma_20
- sma_50
- close_minus_sma_50
- ema_9
- ema_21
- ema9_minus_ema21
- bb_upper
- bb_lower
- bb_bandwidth
- bb_percent_b
- atr_14
- roll_std_5
- roll_std_21
- close_lag_1
- ret1_lag_1
- close_lag_2
- ret1_lag_2
- close_lag_3
- ret1_lag_3
- close_lag_5
- ret1_lag_5
- close_lag_7
- ret1_lag_7
- close_lag_14
- ret1_lag_14
- close_lag_21
- ret1_lag_21
- dayofweek
- month
- quarter
- target_ret_7d
