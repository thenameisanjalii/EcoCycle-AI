"""
EcoCycle AI — Hyperparameter Optimization Configuration Module
Task 2M.1 — Advanced Model Design & Hyperparameter Optimization Plan

Defines:
1. Search spaces for XGBoost, LightGBM, CatBoost
2. Optimization protocol and cross-validation splitting
3. Primary selection metric (Validation RMSE) and secondary metrics
4. Early stopping policies and computational resource constraints
5. Strict Test partition quarantine enforcement
"""

import os
from typing import Dict, Any, List
from .config import RANDOM_SEED

# Strict Test Quarantine Enforcement
TEST_PARTITION_QUARANTINE = True

# Metrics Specification
PRIMARY_SELECTION_METRIC = "RMSE"
SECONDARY_SELECTION_METRICS = ["MAE", "R2"]

# Optimization Protocol Settings
TUNING_PROTOCOL = {
    "search_method": "RandomizedSearchCV",
    "n_iter_per_model": 20,
    "scoring_metric": "neg_root_mean_squared_error",
    "random_state": RANDOM_SEED,
    "cv_strategy": "PredefinedSplit",
    "description": "Predefined train/validation split (Train=81,545 rows / 97 cells; Val=16,606 rows / 21 cells). Test partition is NEVER accessed.",
    "early_stopping_rounds": 25,
    "min_meaningful_improvement_soh_rmse": 0.02,   # Minimum 0.02% RMSE reduction to qualify over baseline (0.6805%)
    "min_meaningful_improvement_rul_rmse": 10.0,    # Minimum 10.0 cycles RMSE reduction over baseline (247.95 cyc)
}

# -------------------------------------------------------------
# Hyperparameter Search Spaces
# -------------------------------------------------------------

# XGBoost Search Space
XGBOOST_PARAM_DISTRIBUTIONS = {
    "n_estimators": [100, 150, 200, 300],
    "learning_rate": [0.03, 0.05, 0.08, 0.1],
    "max_depth": [4, 6, 8],
    "subsample": [0.7, 0.85, 1.0],
    "colsample_bytree": [0.7, 0.85, 1.0],
    "reg_alpha": [0.0, 0.1, 0.5, 1.0],
    "reg_lambda": [1.0, 3.0, 5.0, 10.0],
    "min_child_weight": [1, 3, 5],
}

# LightGBM Search Space
LIGHTGBM_PARAM_DISTRIBUTIONS = {
    "n_estimators": [100, 150, 200, 300],
    "learning_rate": [0.03, 0.05, 0.08, 0.1],
    "num_leaves": [20, 31, 63, 127],
    "max_depth": [-1, 6, 8, 10],
    "min_child_samples": [20, 50, 100],
    "subsample": [0.7, 0.85, 1.0],
    "colsample_bytree": [0.7, 0.85, 1.0],
    "reg_alpha": [0.0, 0.1, 0.5, 1.0],
    "reg_lambda": [1.0, 3.0, 5.0, 10.0],
}

# CatBoost Search Space
CATBOOST_PARAM_DISTRIBUTIONS = {
    "iterations": [150, 250, 350, 500],
    "learning_rate": [0.03, 0.05, 0.08, 0.1],
    "depth": [4, 6, 8],
    "l2_leaf_reg": [1.0, 3.0, 5.0, 10.0],
    "subsample": [0.8, 1.0],
}

# Combined Registry
ADVANCED_SEARCH_SPACES: Dict[str, Dict[str, List[Any]]] = {
    "xgboost": XGBOOST_PARAM_DISTRIBUTIONS,
    "lightgbm": LIGHTGBM_PARAM_DISTRIBUTIONS,
    "catboost": CATBOOST_PARAM_DISTRIBUTIONS,
}

# Locked Baseline Benchmark Records (Task 2L.3)
LOCKED_BASELINE_BENCHMARKS = {
    "SOH": {
        "model_id": "soh_hist_gradient_boosting",
        "val_mae": 0.4245,
        "val_rmse": 0.6805,
        "val_r2": 0.9818,
        "test_mae": 0.3442,
        "test_rmse": 0.5896,
        "test_r2": 0.9815,
        "designation": "FINAL BASELINE WINNER — NOT FINAL PRODUCTION MODEL"
    },
    "RUL": {
        "model_id": "rul_hist_gradient_boosting",
        "val_mae": 130.99,
        "val_rmse": 247.95,
        "val_r2": 0.5440,
        "test_mae": 113.79,
        "test_rmse": 174.33,
        "test_r2": 0.8449,
        "designation": "FINAL BASELINE WINNER — NOT FINAL PRODUCTION MODEL"
    }
}
