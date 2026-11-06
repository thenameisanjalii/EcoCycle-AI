"""
EcoCycle AI — Task 2L.1 Baseline Modeling Configuration
Defines locked parameters, feature sets, target specifications, and paths.
"""
import os

# 1. Reproducibility
RANDOM_SEED = 42

# 2. Paths
BASE_DIR = r"C:\Users\patid\.gemini\antigravity\scratch\EcoCycle-AI"
RAW_DATA_PATH = r"C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv"
EXPECTED_RAW_SHA256 = "0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88"

DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
PREPROCESSORS_DIR = os.path.join(ARTIFACTS_DIR, "preprocessors")
MODELS_DIR = os.path.join(ARTIFACTS_DIR, "models", "task_2l")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "modeling")

PROCESSED_DATA_PATHS = {
    "train_soh": os.path.join(DATA_DIR, "train_soh.csv"),
    "val_soh": os.path.join(DATA_DIR, "val_soh.csv"),
    "test_soh": os.path.join(DATA_DIR, "test_soh.csv"),
    "train_rul": os.path.join(DATA_DIR, "train_rul.csv"),
    "val_rul": os.path.join(DATA_DIR, "val_rul.csv"),
    "test_rul": os.path.join(DATA_DIR, "test_rul.csv"),
}

PREPROCESSOR_PATHS = {
    "soh": os.path.join(PREPROCESSORS_DIR, "preprocessor_soh.joblib"),
    "rul": os.path.join(PREPROCESSORS_DIR, "preprocessor_rul.joblib"),
}

# 3. Targets
TARGET_SOH = "SOH"
TARGET_RUL = "RUL"

TARGET_SPECS = {
    "SOH": {
        "column": "SOH",
        "units": "%",
        "type": "continuous_regression",
        "clip_gt_100": False,
        "description": "State of Health (percentage capacity retention relative to nominal capacity)"
    },
    "RUL": {
        "column": "RUL",
        "units": "cycles",
        "type": "continuous_regression",
        "formula": "max(cycle_battery) - cycle",
        "description": "Remaining Useful Life in operating cycles until nominal test life endpoint"
    }
}

# 4. Features Specification
FEATURE_COLUMNS = [
    "IR",
    "QCharge",
    "Tavg",
    "Tmax",
    "Tmin",
    "chargetime",
    "cycle",
    "IR_is_zero",
    "temp_sensor_fault",
    "IR_lag1",
    "IR_delta",
    "QCharge_lag1",
    "QCharge_delta",
    "Tavg_lag1",
    "Tavg_delta",
    "chargetime_lag1",
    "chargetime_delta"
]

CONTINUOUS_FEATURES = [
    "IR",
    "QCharge",
    "Tavg",
    "Tmax",
    "Tmin",
    "chargetime",
    "cycle",
    "IR_lag1",
    "IR_delta",
    "QCharge_lag1",
    "QCharge_delta",
    "Tavg_lag1",
    "Tavg_delta",
    "chargetime_lag1",
    "chargetime_delta"
]

BINARY_FEATURES = [
    "IR_is_zero",
    "temp_sensor_fault"
]

METADATA_COLUMNS = [
    "battery_id",
    "cycle"
]

FORBIDDEN_COLUMNS_SOH = [
    "battery_id",
    "QDischarge",
    "SOH",
    "RUL",
    "max_cycle",
    "final_cycle",
    "terminal_cycle"
]

FORBIDDEN_COLUMNS_RUL = [
    "battery_id",
    "QDischarge",
    "SOH",
    "RUL",
    "max_cycle",
    "final_cycle",
    "terminal_cycle"
]

# 5. Baseline Model Hyperparameters
BASELINE_MODEL_CONFIGS = {
    "dummy": {
        "class": "DummyRegressor",
        "params": {
            "strategy": "mean"
        },
        "requires_scaling": False,
        "description": "Non-informative empirical mean prior baseline"
    },
    "ridge": {
        "class": "Ridge",
        "pipeline": True,
        "scaler": "RobustScaler",
        "params": {
            "alpha": 1.0,
            "random_state": RANDOM_SEED
        },
        "requires_scaling": True,
        "description": "L2-regularized linear baseline with outlier-resilient feature scaling"
    },
    "random_forest": {
        "class": "RandomForestRegressor",
        "params": {
            "n_estimators": 100,
            "max_depth": 15,
            "min_samples_leaf": 4,
            "random_state": RANDOM_SEED,
            "n_jobs": -1
        },
        "requires_scaling": False,
        "description": "Non-linear bagged decision tree ensemble with regularized depth"
    },
    "hist_gradient_boosting": {
        "class": "HistGradientBoostingRegressor",
        "params": {
            "max_iter": 100,
            "min_samples_leaf": 20,
            "random_state": RANDOM_SEED
        },
        "requires_scaling": False,
        "description": "Fast histogram-binned gradient boosting tree ensemble"
    }
}

# 6. Evaluation Metrics
PRIMARY_SELECTION_METRIC = "RMSE"
METRICS = ["MAE", "RMSE", "R2"]

# 7. Partition Constraints
EXPECTED_PARTITIONS = {
    "train": {"batteries": 97, "rows": 81545},
    "val": {"batteries": 21, "rows": 16606},
    "test": {"batteries": 21, "rows": 18512}
}
