# Phase 4 — Walk-forward validation report

Generated: 2026-09-23T21:26:25  ·  runtime: 39s

`TimeSeriesSplit(n_splits=5, gap=7)` — no shuffling, test window always after train window. The gap purges 7 rows between train and test because 7-day targets of the last train rows overlap the test period. Features: the 43 engineered columns (no Date/OHLCV). Target: `target_ret_7d`.

Settings: RF n_estimators=300, XGB n_estimators=300, GBR n_estimators=200, ElasticNet alpha=0.001. Metals are COMEX futures (`GC=F`, `SI=F`), not MCX spot.

Values are means over the folds. Baselines: `baseline_mean` predicts the training-fold mean return; `baseline_majority_sign` predicts the training-fold majority direction (direction accuracy only). MAPE is unstable when true returns are close to zero.

## INR=X

| model | MAE | RMSE | R² | MAPE | dir. acc. | beats mean (RMSE) | beats naive direction |
|---|---|---|---|---|---|---|---|
| random_forest | 0.0090 | 0.0110 | -1.6047 | 8.2797 | 0.4595 | no | no |
| xgboost | 0.0078 | 0.0097 | -0.9269 | 6.0441 | 0.4539 | no | no |
| ridge | 0.0065 | 0.0082 | -0.4012 | 4.2198 | 0.4354 | no | no |
| elasticnet | 0.0057 | 0.0074 | -0.1334 | 2.6509 | 0.5388 | no | no |
| gradient_boosting | 0.0091 | 0.0112 | -1.6228 | 6.9164 | 0.4557 | no | no |
| baseline_mean | 0.0054 | 0.0071 | -0.0494 | 2.0954 | 0.5812 |  |  |
| baseline_majority_sign | – | – | – | – | 0.5166 |  |  |

## EURUSD=X

| model | MAE | RMSE | R² | MAPE | dir. acc. | beats mean (RMSE) | beats naive direction |
|---|---|---|---|---|---|---|---|
| random_forest | 0.0118 | 0.0151 | -0.9892 | 7.7927 | 0.4781 | no | no |
| xgboost | 0.0125 | 0.0159 | -1.1734 | 8.5768 | 0.4683 | no | no |
| ridge | 0.0140 | 0.0167 | -2.5308 | 8.8790 | 0.4874 | no | no |
| elasticnet | 0.0127 | 0.0153 | -1.6618 | 6.4438 | 0.4615 | no | no |
| gradient_boosting | 0.0123 | 0.0155 | -1.0536 | 8.2705 | 0.4621 | no | no |
| baseline_mean | 0.0088 | 0.0114 | -0.0134 | 1.1275 | 0.4948 |  |  |
| baseline_majority_sign | – | – | – | – | 0.4701 |  |  |

## GBPUSD=X

| model | MAE | RMSE | R² | MAPE | dir. acc. | beats mean (RMSE) | beats naive direction |
|---|---|---|---|---|---|---|---|
| random_forest | 0.0125 | 0.0159 | -0.6555 | 2.8278 | 0.4669 | no | yes |
| xgboost | 0.0133 | 0.0166 | -0.8220 | 3.6266 | 0.4743 | no | yes |
| ridge | 0.0131 | 0.0160 | -0.9556 | 3.7815 | 0.4959 | no | yes |
| elasticnet | 0.0121 | 0.0149 | -0.6349 | 3.2078 | 0.5002 | no | yes |
| gradient_boosting | 0.0120 | 0.0152 | -0.5235 | 2.9093 | 0.4897 | no | yes |
| baseline_mean | 0.0098 | 0.0126 | -0.0251 | 1.0574 | 0.4522 |  |  |
| baseline_majority_sign | – | – | – | – | 0.4626 |  |  |

## GC=F

| model | MAE | RMSE | R² | MAPE | dir. acc. | beats mean (RMSE) | beats naive direction |
|---|---|---|---|---|---|---|---|
| random_forest | 0.0260 | 0.0332 | -0.4190 | 4.9839 | 0.5414 | no | no |
| xgboost | 0.0271 | 0.0344 | -0.5156 | 5.1559 | 0.5242 | no | no |
| ridge | 0.0265 | 0.0335 | -0.4785 | 3.6620 | 0.4988 | no | no |
| elasticnet | 0.0250 | 0.0318 | -0.2777 | 3.3084 | 0.4905 | no | no |
| gradient_boosting | 0.0285 | 0.0361 | -0.6987 | 5.8332 | 0.5484 | no | no |
| baseline_mean | 0.0223 | 0.0288 | -0.0321 | 1.7193 | 0.5720 |  |  |
| baseline_majority_sign | – | – | – | – | 0.5720 |  |  |

## SI=F

| model | MAE | RMSE | R² | MAPE | dir. acc. | beats mean (RMSE) | beats naive direction |
|---|---|---|---|---|---|---|---|
| random_forest | 0.0665 | 0.0810 | -0.9297 | 5.8934 | 0.4570 | no | no |
| xgboost | 0.0764 | 0.0928 | -1.7873 | 8.8429 | 0.4627 | no | no |
| ridge | 0.0876 | 0.1062 | -3.0042 | 8.0324 | 0.4748 | no | no |
| elasticnet | 0.0772 | 0.0918 | -2.1754 | 7.6272 | 0.4646 | no | no |
| gradient_boosting | 0.0761 | 0.0923 | -1.7514 | 7.6746 | 0.4652 | no | no |
| baseline_mean | 0.0454 | 0.0595 | -0.0084 | 1.3248 | 0.5577 |  |  |
| baseline_majority_sign | – | – | – | – | 0.5577 |  |  |

## Did the models beat the naive baselines?

- Lower mean RMSE than `baseline_mean`: **0 of 25** model×asset pairs
- Higher direction accuracy than both baselines: **5 of 25** pairs

Fold-level scores (including baselines) are in `artifacts/metrics_cv.csv`. Plots of the last fold are in `artifacts/plots/`. Accuracy may be modest; no winner is picked here (Phase 5).
