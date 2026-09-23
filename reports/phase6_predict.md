# Phase 6 — Inference report

Generated: 2026-09-23T21:58:31

Output of `python -m src.predict <ticker>` for each asset (real CLI runs, latest cached row). `as_of` is the date of the feature row used. No refit, no CV, no Yahoo call: features come from the `data/` cache and the model from `artifacts/models/`.

**Experimental, not investment advice.** Per `reports/phase5_selection.md`, every saved winner loses to `baseline_mean` on RMSE (`beats_baseline_rmse` is false for all five) and only GBPUSD=X beats both direction baselines. All five predicted 7-day returns are under 1% in magnitude. `GC=F` and `SI=F` are COMEX futures, not MCX spot.

## INR=X

```json
{
  "ticker": "INR=X",
  "as_of": "2026-09-22",
  "pred_return_7d": 0.001695136261097704,
  "direction": "up",
  "model_name": "elasticnet",
  "model_path": "artifacts/models/INR_X_elasticnet.joblib",
  "last_close": 95.58000183105467,
  "beats_baseline_rmse": false,
  "beats_baseline_direction": false
}
```

## EURUSD=X

```json
{
  "ticker": "EURUSD=X",
  "as_of": "2026-09-22",
  "pred_return_7d": 0.001268205776579938,
  "direction": "up",
  "model_name": "ridge",
  "model_path": "artifacts/models/EURUSD_X_ridge.joblib",
  "last_close": 1.145213007926941,
  "beats_baseline_rmse": false,
  "beats_baseline_direction": false
}
```

## GBPUSD=X

```json
{
  "ticker": "GBPUSD=X",
  "as_of": "2026-09-22",
  "pred_return_7d": -0.0005563820389834033,
  "direction": "down",
  "model_name": "elasticnet",
  "model_path": "artifacts/models/GBPUSD_X_elasticnet.joblib",
  "last_close": 1.3356306552886963,
  "beats_baseline_rmse": false,
  "beats_baseline_direction": true
}
```

## GC=F

```json
{
  "ticker": "GC=F",
  "as_of": "2026-09-22",
  "pred_return_7d": -0.00022384291008135308,
  "direction": "down",
  "model_name": "gradient_boosting",
  "model_path": "artifacts/models/GC_F_gradient_boosting.joblib",
  "last_close": 4363.39990234375,
  "beats_baseline_rmse": false,
  "beats_baseline_direction": false
}
```

## SI=F

```json
{
  "ticker": "SI=F",
  "as_of": "2026-09-22",
  "pred_return_7d": 0.006255365678867834,
  "direction": "up",
  "model_name": "ridge",
  "model_path": "artifacts/models/SI_F_ridge.joblib",
  "last_close": 66.16999816894531,
  "beats_baseline_rmse": false,
  "beats_baseline_direction": false
}
```

## Historical `--as-of` example

`python -m src.predict GC=F --as-of 2026-06-30` (in-sample: the model was trained on rows through 2026-09-11, so this is not a real forecast).

```json
{
  "ticker": "GC=F",
  "as_of": "2026-06-30",
  "pred_return_7d": 0.006101154656358828,
  "direction": "up",
  "model_name": "gradient_boosting",
  "model_path": "artifacts/models/GC_F_gradient_boosting.joblib",
  "last_close": 4038.5,
  "beats_baseline_rmse": false,
  "beats_baseline_direction": false
}
```

## Determinism

`python -m src.predict GC=F` was run twice and the outputs were byte-identical (`diff` empty).
