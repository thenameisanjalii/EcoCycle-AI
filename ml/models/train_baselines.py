"""
EcoCycle AI — Baseline Model Training Module (Task 2L.2)
Trains Dummy, Ridge, Random Forest, and HistGradientBoosting baselines
strictly on the Training partition (81,545 rows, 97 batteries).
"""
import time
import joblib
from .baseline_models import create_soh_baseline_models, create_rul_baseline_models
from .config import FEATURE_COLUMNS, FORBIDDEN_COLUMNS_SOH, FORBIDDEN_COLUMNS_RUL

def train_soh_models(X_train, y_train):
    """
    Fits all 4 SOH baseline models on X_train, y_train.
    Asserts absence of forbidden features.
    """
    # Programmatic assertion of feature purity
    cols = list(X_train.columns)
    assert cols == FEATURE_COLUMNS, f"Feature columns mismatch: {cols} vs {FEATURE_COLUMNS}"
    for forbidden in FORBIDDEN_COLUMNS_SOH:
        assert forbidden not in cols, f"Forbidden feature present in X: {forbidden}"
        
    models = create_soh_baseline_models()
    trained_models = {}
    training_times = {}
    
    for name, model in models.items():
        print(f"  Training SOH model: {name}...")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        elapsed = time.perf_counter() - t0
        trained_models[name] = model
        training_times[name] = round(elapsed, 4)
        
    return trained_models, training_times


def train_rul_models(X_train, y_train):
    """
    Fits all 4 RUL baseline models on X_train, y_train.
    Asserts absence of forbidden features.
    """
    cols = list(X_train.columns)
    assert cols == FEATURE_COLUMNS, f"Feature columns mismatch: {cols} vs {FEATURE_COLUMNS}"
    for forbidden in FORBIDDEN_COLUMNS_RUL:
        assert forbidden not in cols, f"Forbidden feature present in X: {forbidden}"
        
    models = create_rul_baseline_models()
    trained_models = {}
    training_times = {}
    
    for name, model in models.items():
        print(f"  Training RUL model: {name}...")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        elapsed = time.perf_counter() - t0
        trained_models[name] = model
        training_times[name] = round(elapsed, 4)
        
    return trained_models, training_times
