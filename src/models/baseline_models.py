"""
EcoCycle AI — Baseline Model Factory Module
Defines standard model instantiations for SOH and RUL baselines.
All models are strictly instantiated un-fitted with fixed random_state=42.
"""
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from .config import RANDOM_SEED, CONTINUOUS_FEATURES

def create_soh_baseline_models():
    """
    Instantiates the 4 contracted baseline models for SOH regression.
    Returns:
        dict: model_id -> un-fitted estimator or Pipeline
    """
    models = {
        "dummy": DummyRegressor(
            strategy="mean"
        ),
        "ridge": Pipeline([
            ("scaler", RobustScaler()),
            ("model", Ridge(alpha=1.0, random_state=RANDOM_SEED))
        ]),
        "random_forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_leaf=4,
            random_state=RANDOM_SEED,
            n_jobs=-1
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=100,
            min_samples_leaf=20,
            random_state=RANDOM_SEED
        )
    }
    return models


def create_rul_baseline_models():
    """
    Instantiates the 4 contracted baseline models for RUL regression.
    Returns:
        dict: model_id -> un-fitted estimator or Pipeline
    """
    models = {
        "dummy": DummyRegressor(
            strategy="mean"
        ),
        "ridge": Pipeline([
            ("scaler", RobustScaler()),
            ("model", Ridge(alpha=1.0, random_state=RANDOM_SEED))
        ]),
        "random_forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_leaf=4,
            random_state=RANDOM_SEED,
            n_jobs=-1
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=100,
            min_samples_leaf=20,
            random_state=RANDOM_SEED
        )
    }
    return models
