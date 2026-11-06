"""
EcoCycle AI — Advanced Model Factory Module
Task 2M.1 — Advanced Model Design

Defines model factories for advanced gradient boosting architectures:
1. XGBoost Regressor (xgb.XGBRegressor)
2. LightGBM Regressor (lgb.LGBMRegressor)
3. CatBoost Regressor (cb.CatBoostRegressor)
4. HistGradientBoosting Regressor (sklearn benchmark baseline)

All models are instantiated UN-FITTED with fixed random_state=42.
"""

from typing import Dict, Any
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
from sklearn.ensemble import HistGradientBoostingRegressor

from .config import RANDOM_SEED

# Architectural Rationale Registry
MODEL_ARCHITECTURAL_RATIONALE = {
    "xgboost": {
        "framework": "XGBoost",
        "description": "Extreme Gradient Boosting with 2nd-order Taylor expansion objective",
        "key_mechanisms": [
            "Exact and histogram-based split finding for rapid feature evaluations",
            "Explicit L1 (reg_alpha) and L2 (reg_lambda) leaf weight penalization to suppress sensor noise overfitting",
            "Subsample and colsample_bytree randomization to improve inter-battery cell generalization",
            "Shrinkage step (learning_rate) preventing premature convergence on early degradation cycles"
        ],
        "hypothesis": "Superior capacity to handle multicollinear lagged/delta features while strictly regularizing against noisy cycle outliers."
    },
    "lightgbm": {
        "framework": "LightGBM",
        "description": "Histogram-based gradient boosting with leaf-wise (best-first) tree growth",
        "key_mechanisms": [
            "Leaf-wise tree growth with depth limits to optimize objective loss directly rather than level-wise symmetry",
            "Histogram discretization of continuous degradation measurements into discrete quantile bins",
            "Gradient-based One-Side Sampling (GOSS) and Exclusive Feature Bundling (EFB) for fast computation",
            "Min child samples and min child weight constraints to ensure robust leaf coverage"
        ],
        "hypothesis": "Enhanced ability to resolve non-linear degradation kinks (knees) near EOL with lower computational overhead."
    },
    "catboost": {
        "framework": "CatBoost",
        "description": "Symmetric / oblivious decision trees with ordered boosting",
        "key_mechanisms": [
            "Oblivious (symmetric) decision tree structure providing strong inductive bias against overfitting",
            "Ordered boosting to eliminate prediction shift and gradient target leakage inherent in sequential tabular datasets",
            "Efficient numerical feature discretization with optimal split point search",
            "L2 leaf regularization and random subspace sampling"
        ],
        "hypothesis": "Highest resistance to distribution shift across unseen test batteries, preventing over-optimistic validation fit."
    },
    "hist_gradient_boosting": {
        "framework": "scikit-learn HistGradientBoosting (Baseline Benchmark)",
        "description": "Locked Task 2L.3 baseline winner retained as immutable benchmark",
        "key_mechanisms": [
            "Scikit-learn histogram-based gradient boosting",
            "Default tree parameters (max_iter=100, min_samples_leaf=20, random_state=42)"
        ],
        "hypothesis": "Immutable comparison benchmark; all advanced models must beat this baseline meaningfully."
    }
}


def create_soh_advanced_models() -> Dict[str, Any]:
    """
    Instantiates un-fitted advanced regression models for SOH regression.
    Fixed random_state=RANDOM_SEED (42).

    Returns:
        dict: model_id -> un-fitted estimator instance
    """
    models = {
        "xgboost": xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.1,
            reg_lambda=1.0,
            tree_method="hist",
            objective="reg:squarederror",
            random_state=RANDOM_SEED,
            n_jobs=-1
        ),
        "lightgbm": lgb.LGBMRegressor(
            n_estimators=100,
            learning_rate=0.05,
            num_leaves=31,
            max_depth=6,
            min_child_samples=20,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbose=-1
        ),
        "catboost": cb.CatBoostRegressor(
            iterations=150,
            learning_rate=0.05,
            depth=6,
            l2_leaf_reg=3.0,
            random_seed=RANDOM_SEED,
            verbose=0,
            thread_count=-1
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=100,
            min_samples_leaf=20,
            random_state=RANDOM_SEED
        )
    }
    return models


def create_rul_advanced_models() -> Dict[str, Any]:
    """
    Instantiates un-fitted advanced regression models for RUL regression.
    Fixed random_state=RANDOM_SEED (42).

    Returns:
        dict: model_id -> un-fitted estimator instance
    """
    models = {
        "xgboost": xgb.XGBRegressor(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.1,
            reg_lambda=1.0,
            tree_method="hist",
            objective="reg:squarederror",
            random_state=RANDOM_SEED,
            n_jobs=-1
        ),
        "lightgbm": lgb.LGBMRegressor(
            n_estimators=150,
            learning_rate=0.05,
            num_leaves=31,
            max_depth=6,
            min_child_samples=20,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbose=-1
        ),
        "catboost": cb.CatBoostRegressor(
            iterations=200,
            learning_rate=0.05,
            depth=6,
            l2_leaf_reg=3.0,
            random_seed=RANDOM_SEED,
            verbose=0,
            thread_count=-1
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=100,
            min_samples_leaf=20,
            random_state=RANDOM_SEED
        )
    }
    return models
