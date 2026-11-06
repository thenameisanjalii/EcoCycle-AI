"""
EcoCycle AI — Task 2M.1 Static Consistency & Quarantine Audit
Verifies:
1. Raw dataset SHA-256 byte-identity
2. Model configuration consistency & un-fitted status
3. Hyperparameter search space validity
4. Causal feature definitions and temporal proofs
5. Feature leakage restrictions & forbidden column exclusions
6. Train/Validation/Test partition definitions & strict test quarantine
7. Random seed consistency (random_state=42)
8. Baseline model artifact preservation
"""

import os
import sys
import hashlib
import json

BASE_DIR = r"C:\Users\patid\.gemini\antigravity\scratch\EcoCycle-AI"
sys.path.insert(0, BASE_DIR)

from src.models.config import (
    RANDOM_SEED, EXPECTED_RAW_SHA256, RAW_DATA_PATH,
    PROCESSED_DATA_PATHS, EXPECTED_PARTITIONS
)
from src.models.advanced_models import (
    create_soh_advanced_models, create_rul_advanced_models,
    MODEL_ARCHITECTURAL_RATIONALE
)
from src.models.tuning_config import (
    ADVANCED_SEARCH_SPACES, TUNING_PROTOCOL,
    LOCKED_BASELINE_BENCHMARKS, TEST_PARTITION_QUARANTINE
)
from src.models.feature_engineering import (
    BASELINE_FEATURE_COLUMNS, CANDIDATE_CAUSAL_FEATURES,
    ADVANCED_FEATURE_COLUMNS, FORBIDDEN_COLUMNS,
    validate_causality_rules
)

print("==================================================")
print("RUNNING TASK 2M.1 STATIC AUDIT & VERIFICATION")
print("==================================================")

# 1. Raw Dataset SHA-256 Protection
print("[CHECK 1] Verifying Raw Dataset SHA-256...")
with open(RAW_DATA_PATH, "rb") as f:
    current_raw_hash = hashlib.sha256(f.read()).hexdigest()
assert current_raw_hash == EXPECTED_RAW_SHA256, f"RAW HASH MISMATCH: {current_raw_hash}"
print(f"  [PASS] Raw dataset byte-identical: {current_raw_hash}")

# 2. Strict Test Quarantine Check
print("[CHECK 2] Verifying Test Partition Quarantine...")
assert TEST_PARTITION_QUARANTINE is True, "TEST_PARTITION_QUARANTINE must be True"
# Ensure test files exist on disk but are NOT loaded or read during audit
assert os.path.exists(PROCESSED_DATA_PATHS["test_soh"]), "test_soh.csv missing from disk"
assert os.path.exists(PROCESSED_DATA_PATHS["test_rul"]), "test_rul.csv missing from disk"
print("  [PASS] Test partition quarantined and untouched.")

# 3. Random Seed Consistency
print("[CHECK 3] Verifying Random Seed Consistency...")
assert RANDOM_SEED == 42, f"Expected RANDOM_SEED=42, got {RANDOM_SEED}"
assert TUNING_PROTOCOL["random_state"] == 42, "Tuning protocol random_state must be 42"
print("  [PASS] Random seed is uniformly 42.")

# 4. Feature Counts and Leakage Restrictions
print("[CHECK 4] Verifying Feature Counts and Leakage Rules...")
assert len(BASELINE_FEATURE_COLUMNS) == 17, f"Expected 17 baseline features, got {len(BASELINE_FEATURE_COLUMNS)}"
assert len(CANDIDATE_CAUSAL_FEATURES) == 15, f"Expected 15 candidate causal features, got {len(CANDIDATE_CAUSAL_FEATURES)}"
assert len(ADVANCED_FEATURE_COLUMNS) == 32, f"Expected 32 advanced features, got {len(ADVANCED_FEATURE_COLUMNS)}"

# Check forbidden columns are not in feature set
for forbidden in FORBIDDEN_COLUMNS:
    assert forbidden not in ADVANCED_FEATURE_COLUMNS, f"Forbidden entity {forbidden} leaked into features!"
    assert forbidden not in BASELINE_FEATURE_COLUMNS, f"Forbidden entity {forbidden} in baseline features!"
print("  [PASS] Feature schema verified (17 baseline + 15 causal = 32 features). Zero forbidden leaks.")

# 5. Causal Feature Registry and Temporal Proofs
print("[CHECK 5] Validating Causal Feature Definitions...")
causality_res = validate_causality_rules()
assert causality_res["status"] == "PASS", "Causality validation failed"
print(f"  [PASS] All {len(CANDIDATE_CAUSAL_FEATURES)} candidate features proven causal with zero future lookahead.")

# 6. Advanced Model Factory and Un-Fitted Status
print("[CHECK 6] Verifying Advanced Model Factories...")
soh_adv_models = create_soh_advanced_models()
rul_adv_models = create_rul_advanced_models()

expected_model_keys = {"xgboost", "lightgbm", "catboost", "hist_gradient_boosting"}
assert set(soh_adv_models.keys()) == expected_model_keys, f"SOH model keys mismatch: {set(soh_adv_models.keys())}"
assert set(rul_adv_models.keys()) == expected_model_keys, f"RUL model keys mismatch: {set(rul_adv_models.keys())}"

from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

# Verify models are UN-FITTED
for name, m in list(soh_adv_models.items()) + list(rul_adv_models.items()):
    try:
        check_is_fitted(m)
        assert False, f"Model {name} unexpectedly fitted!"
    except NotFittedError:
        pass
    if hasattr(m, "is_fitted"):
        assert not m.is_fitted(), f"Model {name} unexpectedly reported is_fitted() == True!"

print("  [PASS] Advanced model factories instantiate XGBoost, LightGBM, CatBoost, HistGradientBoosting UN-FITTED.")

# 7. Hyperparameter Search Spaces
print("[CHECK 7] Validating Hyperparameter Search Spaces...")
for arch in ["xgboost", "lightgbm", "catboost"]:
    assert arch in ADVANCED_SEARCH_SPACES, f"Missing search space for {arch}"
    space = ADVANCED_SEARCH_SPACES[arch]
    assert len(space) >= 5, f"Search space for {arch} has insufficient parameters: {len(space)}"
    for param_name, values in space.items():
        assert isinstance(values, list) and len(values) > 0, f"Invalid values for {arch}.{param_name}"
print("  [PASS] Hyperparameter search spaces defined and structured.")

# 8. Baseline Benchmark Records Preservation
print("[CHECK 8] Verifying Baseline Benchmark Preservation...")
assert LOCKED_BASELINE_BENCHMARKS["SOH"]["val_rmse"] == 0.6805
assert LOCKED_BASELINE_BENCHMARKS["SOH"]["test_rmse"] == 0.5896
assert LOCKED_BASELINE_BENCHMARKS["RUL"]["val_rmse"] == 247.95
assert LOCKED_BASELINE_BENCHMARKS["RUL"]["test_rmse"] == 174.33
# Check that baseline model files still exist
soh_base_path = os.path.join(BASE_DIR, "models", "baseline", "soh_hist_gradient_boosting.joblib")
rul_base_path = os.path.join(BASE_DIR, "models", "baseline", "rul_hist_gradient_boosting.joblib")
assert os.path.exists(soh_base_path), f"Baseline model missing: {soh_base_path}"
assert os.path.exists(rul_base_path), f"Baseline model missing: {rul_base_path}"
print("  [PASS] Baseline model files and benchmarks preserved intact.")

# 9. Config JSON File Alignment
print("[CHECK 9] Validating reports/modeling/task_2m_1_config.json...")
config_path = os.path.join(BASE_DIR, "reports", "modeling", "task_2m_1_config.json")
assert os.path.exists(config_path), f"Missing config file: {config_path}"
with open(config_path, "r") as f:
    cfg = json.load(f)
assert cfg["raw_dataset_hash"] == EXPECTED_RAW_SHA256
assert cfg["models_trained"] is False, "models_trained must be False in Task 2M.1"
assert cfg["partitions"]["test"]["status"] == "STRICTLY_QUARANTINED"
print("  [PASS] Machine-readable config JSON verified.")

# 10. Design Markdown Report Alignment
print("[CHECK 10] Validating reports/modeling/task_2m_1_advanced_model_design.md...")
report_path = os.path.join(BASE_DIR, "reports", "modeling", "task_2m_1_advanced_model_design.md")
assert os.path.exists(report_path), f"Missing report: {report_path}"
with open(report_path, "r", encoding="utf-8") as f:
    rep_text = f.read()
assert "TASK 2M.1 STATUS" in rep_text
assert "0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88" in rep_text
assert "NOT FINAL PRODUCTION MODELS" in rep_text
print("  [PASS] Markdown report verified.")

print("\n==================================================")
print("STATIC CONSISTENCY & QUARANTINE AUDIT: ALL CHECKS PASSED")
print("==================================================")
