"""Phase 4: the fixed set of five regressors. Hyperparameters live in config.py."""

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from config import (ELASTICNET_PARAMS, GBR_PARAMS, RF_PARAMS, RIDGE_PARAMS,
                    XGB_PARAMS)


def get_models() -> dict:
    """Fresh, unfitted estimators. Call once per fold so nothing carries over."""
    return {
        "random_forest": RandomForestRegressor(**RF_PARAMS),
        "xgboost": XGBRegressor(**XGB_PARAMS),
        "ridge": make_pipeline(StandardScaler(), Ridge(**RIDGE_PARAMS)),
        "elasticnet": make_pipeline(StandardScaler(), ElasticNet(**ELASTICNET_PARAMS)),
        "gradient_boosting": GradientBoostingRegressor(**GBR_PARAMS),
    }
