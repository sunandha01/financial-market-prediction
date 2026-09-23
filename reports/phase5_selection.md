# Phase 5 — Model selection report

Generated: 2026-09-23T21:43:32

## Selection rule

Among the five ML models only (baselines are never saved): highest **mean directional accuracy** across the 5 walk-forward folds; ties (at 6 decimals) are broken by lower **mean RMSE**. The winning algorithm is then refit on all labelled rows (everything except the last 7 sessions, which have no 7-day-ahead close) and saved to `artifacts/models/`. Scores are from Phase 4 (`TimeSeriesSplit(5, gap=7)`); features and CV settings are unchanged.

## Winner vs the naive baselines

| asset | winner | winner dir. acc. | baseline_mean dir. acc. | baseline_majority_sign dir. acc. | winner RMSE | baseline_mean RMSE | beats mean on RMSE | beats both direction baselines |
|---|---|---|---|---|---|---|---|---|
| INR=X | elasticnet | 0.5388 | 0.5812 | 0.5166 | 0.0074 | 0.0071 | **NO** | **NO** |
| EURUSD=X | ridge | 0.4874 | 0.4948 | 0.4701 | 0.0167 | 0.0114 | **NO** | **NO** |
| GBPUSD=X | elasticnet | 0.5002 | 0.4522 | 0.4626 | 0.0149 | 0.0126 | **NO** | yes |
| GC=F | gradient_boosting | 0.5484 | 0.5720 | 0.5720 | 0.0361 | 0.0288 | **NO** | **NO** |
| SI=F | ridge | 0.4748 | 0.5577 | 0.5577 | 0.1062 | 0.0595 | **NO** | **NO** |

### Verdict per asset

- `INR=X` (elasticnet): **LOSES to the naive baseline on both RMSE and direction.**
- `EURUSD=X` (ridge): **LOSES to the naive baseline on both RMSE and direction.**
- `GBPUSD=X` (elasticnet): Beats both naive direction baselines but **LOSES to baseline_mean on RMSE.**
- `GC=F` (gradient_boosting): **LOSES to the naive baseline on both RMSE and direction.**
- `SI=F` (ridge): **LOSES to the naive baseline on both RMSE and direction.**

## Facts from the Phase 4 run

- 0 of 25 model×asset pairs beat `baseline_mean` on RMSE.
- 5 of 25 pairs beat both direction baselines (all in: GBPUSD=X).
- Gold/silver (`GC=F`, `SI=F` — COMEX futures) naive direction accuracy is high because both drifted upward over 2019–2026; the majority-sign baseline simply rides that drift.
- No 60–65% accuracy claim is supported by these metrics.

## Conclusion

The selection rule produced five saved models, but 5 of 5 winners lose to the training-mean baseline on RMSE and 4 of 5 do not beat both naive direction baselines; only GBPUSD=X clears that bar on direction. Mean directional accuracy across all 25 model×asset pairs ranges from 0.435 to 0.548, and every model has negative mean R², meaning it predicts worse than a constant. The winner is the best of five scored on the same folds it was picked from, so its scores are optimistic, and the refit models have no out-of-sample score at all. These files exist so the pipeline can move forward (Phase 6 needs something to load); they are not evidence of forecasting skill, and any dashboard copy must say forecasts are experimental and not advice.

## Artefacts

- `artifacts/models/{safe_ticker}_{model}.joblib` — dict with `model`, `model_name`, `ticker`, `feature_columns`, `train_rows`, `train_end`
- `artifacts/metrics_summary.csv` — the table above
- `artifacts/feature_importance.csv` and `artifacts/plots/*_importance.png` — tree winners only: `GC=F` (gradient_boosting)
