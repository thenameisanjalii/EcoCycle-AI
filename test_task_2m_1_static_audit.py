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
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from ml.models.config import (
    RANDOM_SEED, EXPECTED_RAW_SHA256, RAW_DATA_PATH,
    PROCESSED_DATA_PATHS, EXPECTED_PARTITIONS
)
from ml.models.advanced_models import (
    create_soh_advanced_models, create_rul_advanced_models,
    MODEL_ARCHITECTURAL_RATIONALE
)
from ml.models.tuning_config import (
    ADVANCED_SEARCH_SPACES, TUNING_PROTOCOL,
    LOCKED_BASELINE_BENCHMARKS, TEST_PARTITION_QUARANTINE
)
from ml.models.feature_engineering import (
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
python -m pytest tests\test_input_validation.py -v
>> python -m pytest tests\test_final_model_loading.py -v
>> python -m pytest tests\test_inference_contract.py -v
>> python -m pytest tests\test_api_integration.py -v
>> python -m pytest tests\test_decision_engine.py -v
>> python -m pytest tests\test_decision_api.py -v
=========================== test session starts ===========================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 13 items                                                         

tests/test_input_validation.py::test_valid_input_dict PASSED         [  7%]
tests/test_input_validation.py::test_valid_input_dataframe PASSED    [ 15%]
tests/test_input_validation.py::test_deterministic_column_ordering PASSED [23%]
tests/test_input_validation.py::test_metadata_segregation PASSED     [ 30%]
tests/test_input_validation.py::test_missing_features_raise_error PASSED [ 38%]
tests/test_input_validation.py::test_nan_features_raise_error PASSED [ 46%]
tests/test_input_validation.py::test_inf_features_raise_error PASSED [ 53%]
tests/test_input_validation.py::test_leakage_qdischarge_rejected PASSED [ 61%]
tests/test_input_validation.py::test_leakage_max_cycle_rejected PASSED [ 69%]
tests/test_input_validation.py::test_cross_target_soh_in_rul_rejected PASSED [ 76%]
tests/test_input_validation.py::test_cross_target_rul_in_soh_rejected PASSED [ 84%]
tests/test_input_validation.py::test_physical_bounds_cycle PASSED    [ 92%]
tests/test_input_validation.py::test_physical_bounds_negative_qcharge PASSED [100%]

=========================== 13 passed in 1.94s ============================
=========================== test session starts ===========================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 8 items                                                          

tests/test_final_model_loading.py::test_registry_initialization PASSED [ 12%]
tests/test_final_model_loading.py::test_soh_model_loading PASSED     [ 25%]
tests/test_final_model_loading.py::test_rul_model_loading PASSED     [ 37%]
tests/test_final_model_loading.py::test_registry_caching PASSED      [ 50%]
tests/test_final_model_loading.py::test_unknown_target_raises_error PASSED [ 62%]
tests/test_final_model_loading.py::test_fail_fast_on_missing_config PASSED [ 75%]
tests/test_final_model_loading.py::test_fail_fast_on_corrupted_config PASSED [ 87%]
tests/test_final_model_loading.py::test_fail_fast_on_hash_mismatch PASSED [100%]

============================ 8 passed in 5.31s ============================
=========================== test session starts ===========================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 6 items                                                          

tests/test_inference_contract.py::test_predict_soh_single_record PASSED [ 16%]
tests/test_inference_contract.py::test_predict_rul_single_record PASSED [ 33%]
tests/test_inference_contract.py::test_predict_all_structure PASSED  [ 50%]
tests/test_inference_contract.py::test_inference_determinism PASSED  [ 66%]
tests/test_inference_contract.py::test_batch_inference_preserves_input PASSED [ 83%]
tests/test_inference_contract.py::test_raw_prediction_unclipped_preservation PASSED [100%]

============================ 6 passed in 7.51s ============================
=========================== test session starts ===========================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 18 items                                                         

tests/test_api_integration.py::test_01_health_endpoint PASSED        [  5%]
tests/test_api_integration.py::test_02_model_info_endpoint PASSED    [ 11%]
tests/test_api_integration.py::test_03_valid_prediction FAILED       [ 16%]
tests/test_api_integration.py::test_04_missing_feature_rejection PASSED [ 22%]
tests/test_api_integration.py::test_05_nan_rejection PASSED          [ 27%]
tests/test_api_integration.py::test_06_inf_rejection PASSED          [ 33%]
tests/test_api_integration.py::test_07_qdischarge_leakage_rejection FAILED [ 38%]
tests/test_api_integration.py::test_08_max_cycle_leakage_rejection FAILED [44%]
tests/test_api_integration.py::test_09_cross_target_leakage_rejection FAILED [ 50%]
tests/test_api_integration.py::test_10_invalid_physical_value FAILED [ 55%]
tests/test_api_integration.py::test_11_deterministic_repeated_prediction FAILED [ 61%]
tests/test_api_integration.py::test_12_batch_prediction PASSED       [ 66%]
tests/test_api_integration.py::test_13_metadata_preservation FAILED  [ 72%]
tests/test_api_integration.py::test_14_raw_prediction_preservation FAILED [77%]
tests/test_api_integration.py::test_15_display_bounding FAILED       [ 83%]
tests/test_api_integration.py::test_16_model_registry_integrity PASSED [ 88%]
tests/test_api_integration.py::test_17_model_artifact_hash_verification PASSED [ 94%]
tests/test_api_integration.py::test_18_malformed_request_handling PASSED [100%]

================================ FAILURES =================================
________________________ test_03_valid_prediction _________________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_03_valid_prediction(valid_cycle_payload):
        resp = client.post("/predict", json=valid_cycle_payload)
>       assert resp.status_code == 200
E       assert 422 == 200
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests\test_api_integration.py:91: AssertionError
__________________ test_07_qdischarge_leakage_rejection ___________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_07_qdischarge_leakage_rejection(valid_cycle_payload):
        bad_payload = valid_cycle_payload.copy()
        bad_payload["QDischarge"] = 1.05
        resp = client.post("/predict", json=bad_payload)
        assert resp.status_code == 422
>       assert "leakage" in resp.text.lower()
E       assert 'leakage' in '{"detail":[{"type":"missing","loc":["body","records"],"msg":"field required","input":{"ir":0.0085,"qcharge":1.065,"tavg":30.2,"tmax":32.5,"tmin":28.0,"chargetime":40.5,"cycle":120.0,"ir_is_zero":0.0,"temp_sensor_fault":0.0,"ir_lag1":0.0084,"ir_delta":0.0001,"qcharge_lag1":1.066,"qcharge_delta":-0.001,"tavg_lag1":30.1,"tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"ir_accel":1.0,"qcharge_accel":1.0,"tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"ir_roll_mean_5":1.0,"ir_roll_std_5":1.0,"qcharge_roll_mean_5":1.0,"qcharge_roll_std_5":1.0,"tavg_roll_mean_5":1.0,"tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","qdischarge":1.05}}]}'
E        +  where '{"detail":[{"type":"missing","loc":["body","records"],"msg":"field required","input":{"ir":0.0085,"qcharge":1.065,"tavg":30.2,"tmax":32.5,"tmin":28.0,"chargetime":40.5,"cycle":120.0,"ir_is_zero":0.0,"temp_sensor_fault":0.0,"ir_lag1":0.0084,"ir_delta":0.0001,"qcharge_lag1":1.066,"qcharge_delta":-0.001,"tavg_lag1":30.1,"tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"ir_accel":1.0,"qcharge_accel":1.0,"tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"ir_roll_mean_5":1.0,"ir_roll_std_5":1.0,"qcharge_roll_mean_5":1.0,"qcharge_roll_std_5":1.0,"tavg_roll_mean_5":1.0,"tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","qdischarge":1.05}}]}' = <built-in method lower of str object at 0x000002201287DAD0>()
E        +    where <built-in method lower of str object at 0x000002201287DAD0> = '{"detail":[{"type":"missing","loc":["body","records"],"msg":"Field required","input":{"IR":0.0085,"QCharge":1.065,"Tavg":30.2,"Tmax":32.5,"Tmin":28.0,"chargetime":40.5,"cycle":120.0,"IR_is_zero":0.0,"temp_sensor_fault":0.0,"IR_lag1":0.0084,"IR_delta":0.0001,"QCharge_lag1":1.066,"QCharge_delta":-0.001,"Tavg_lag1":30.1,"Tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"IR_accel":1.0,"QCharge_accel":1.0,"Tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"IR_roll_mean_5":1.0,"IR_roll_std_5":1.0,"QCharge_roll_mean_5":1.0,"QCharge_roll_std_5":1.0,"Tavg_roll_mean_5":1.0,"Tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","QDischarge":1.05}}]}'.lower
E        +      where '{"detail":[{"type":"missing","loc":["body","records"],"msg":"Field required","input":{"IR":0.0085,"QCharge":1.065,"Tavg":30.2,"Tmax":32.5,"Tmin":28.0,"chargetime":40.5,"cycle":120.0,"IR_is_zero":0.0,"temp_sensor_fault":0.0,"IR_lag1":0.0084,"IR_delta":0.0001,"QCharge_lag1":1.066,"QCharge_delta":-0.001,"Tavg_lag1":30.1,"Tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"IR_accel":1.0,"QCharge_accel":1.0,"Tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"IR_roll_mean_5":1.0,"IR_roll_std_5":1.0,"QCharge_roll_mean_5":1.0,"QCharge_roll_std_5":1.0,"Tavg_roll_mean_5":1.0,"Tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","QDischarge":1.05}}]}' = <Response [422 Unprocessable Entity]>.text

tests\test_api_integration.py:132: AssertionError
___________________ test_08_max_cycle_leakage_rejection ___________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_08_max_cycle_leakage_rejection(valid_cycle_payload):
        bad_payload = valid_cycle_payload.copy()
        bad_payload["max_cycle"] = 1200
        resp = client.post("/predict", json=bad_payload)
        assert resp.status_code == 422
>       assert "leakage" in resp.text.lower()
E       assert 'leakage' in '{"detail":[{"type":"missing","loc":["body","records"],"msg":"field required","input":{"ir":0.0085,"qcharge":1.065,"tavg":30.2,"tmax":32.5,"tmin":28.0,"chargetime":40.5,"cycle":120.0,"ir_is_zero":0.0,"temp_sensor_fault":0.0,"ir_lag1":0.0084,"ir_delta":0.0001,"qcharge_lag1":1.066,"qcharge_delta":-0.001,"tavg_lag1":30.1,"tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"ir_accel":1.0,"qcharge_accel":1.0,"tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"ir_roll_mean_5":1.0,"ir_roll_std_5":1.0,"qcharge_roll_mean_5":1.0,"qcharge_roll_std_5":1.0,"tavg_roll_mean_5":1.0,"tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","max_cycle":1200}}]}'
E        +  where '{"detail":[{"type":"missing","loc":["body","records"],"msg":"field required","input":{"ir":0.0085,"qcharge":1.065,"tavg":30.2,"tmax":32.5,"tmin":28.0,"chargetime":40.5,"cycle":120.0,"ir_is_zero":0.0,"temp_sensor_fault":0.0,"ir_lag1":0.0084,"ir_delta":0.0001,"qcharge_lag1":1.066,"qcharge_delta":-0.001,"tavg_lag1":30.1,"tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"ir_accel":1.0,"qcharge_accel":1.0,"tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"ir_roll_mean_5":1.0,"ir_roll_std_5":1.0,"qcharge_roll_mean_5":1.0,"qcharge_roll_std_5":1.0,"tavg_roll_mean_5":1.0,"tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","max_cycle":1200}}]}'= <built-in method lower of str object at 0x0000022011CDF340>()
E        +    where <built-in method lower of str object at 0x0000022011CDF340> = '{"detail":[{"type":"missing","loc":["body","records"],"msg":"Field required","input":{"IR":0.0085,"QCharge":1.065,"Tavg":30.2,"Tmax":32.5,"Tmin":28.0,"chargetime":40.5,"cycle":120.0,"IR_is_zero":0.0,"temp_sensor_fault":0.0,"IR_lag1":0.0084,"IR_delta":0.0001,"QCharge_lag1":1.066,"QCharge_delta":-0.001,"Tavg_lag1":30.1,"Tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"IR_accel":1.0,"QCharge_accel":1.0,"Tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"IR_roll_mean_5":1.0,"IR_roll_std_5":1.0,"QCharge_roll_mean_5":1.0,"QCharge_roll_std_5":1.0,"Tavg_roll_mean_5":1.0,"Tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","max_cycle":1200}}]}'.lower
E        +      where '{"detail":[{"type":"missing","loc":["body","records"],"msg":"Field required","input":{"IR":0.0085,"QCharge":1.065,"Tavg":30.2,"Tmax":32.5,"Tmin":28.0,"chargetime":40.5,"cycle":120.0,"IR_is_zero":0.0,"temp_sensor_fault":0.0,"IR_lag1":0.0084,"IR_delta":0.0001,"QCharge_lag1":1.066,"QCharge_delta":-0.001,"Tavg_lag1":30.1,"Tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"IR_accel":1.0,"QCharge_accel":1.0,"Tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"IR_roll_mean_5":1.0,"IR_roll_std_5":1.0,"QCharge_roll_mean_5":1.0,"QCharge_roll_std_5":1.0,"Tavg_roll_mean_5":1.0,"Tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","max_cycle":1200}}]}' = <Response [422 Unprocessable Entity]>.text

tests\test_api_integration.py:141: AssertionError
_________________ test_09_cross_target_leakage_rejection __________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_09_cross_target_leakage_rejection(valid_cycle_payload):
        bad_payload = valid_cycle_payload.copy()
        bad_payload["SOH"] = 92.5
        resp = client.post("/predict", json=bad_payload)
        assert resp.status_code == 422
>       assert "leakage" in resp.text.lower()
E       assert 'leakage' in '{"detail":[{"type":"missing","loc":["body","records"],"msg":"field required","input":{"ir":0.0085,"qcharge":1.065,"tavg":30.2,"tmax":32.5,"tmin":28.0,"chargetime":40.5,"cycle":120.0,"ir_is_zero":0.0,"temp_sensor_fault":0.0,"ir_lag1":0.0084,"ir_delta":0.0001,"qcharge_lag1":1.066,"qcharge_delta":-0.001,"tavg_lag1":30.1,"tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"ir_accel":1.0,"qcharge_accel":1.0,"tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"ir_roll_mean_5":1.0,"ir_roll_std_5":1.0,"qcharge_roll_mean_5":1.0,"qcharge_roll_std_5":1.0,"tavg_roll_mean_5":1.0,"tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","soh":92.5}}]}'
E        +  where '{"detail":[{"type":"missing","loc":["body","records"],"msg":"field required","input":{"ir":0.0085,"qcharge":1.065,"tavg":30.2,"tmax":32.5,"tmin":28.0,"chargetime":40.5,"cycle":120.0,"ir_is_zero":0.0,"temp_sensor_fault":0.0,"ir_lag1":0.0084,"ir_delta":0.0001,"qcharge_lag1":1.066,"qcharge_delta":-0.001,"tavg_lag1":30.1,"tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"ir_accel":1.0,"qcharge_accel":1.0,"tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"ir_roll_mean_5":1.0,"ir_roll_std_5":1.0,"qcharge_roll_mean_5":1.0,"qcharge_roll_std_5":1.0,"tavg_roll_mean_5":1.0,"tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","soh":92.5}}]}' = <built-in method lower of str object at 0x0000022011CDF6A0>()
E        +    where <built-in method lower of str object at 0x0000022011CDF6A0> = '{"detail":[{"type":"missing","loc":["body","records"],"msg":"Field required","input":{"IR":0.0085,"QCharge":1.065,"Tavg":30.2,"Tmax":32.5,"Tmin":28.0,"chargetime":40.5,"cycle":120.0,"IR_is_zero":0.0,"temp_sensor_fault":0.0,"IR_lag1":0.0084,"IR_delta":0.0001,"QCharge_lag1":1.066,"QCharge_delta":-0.001,"Tavg_lag1":30.1,"Tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"IR_accel":1.0,"QCharge_accel":1.0,"Tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"IR_roll_mean_5":1.0,"IR_roll_std_5":1.0,"QCharge_roll_mean_5":1.0,"QCharge_roll_std_5":1.0,"Tavg_roll_mean_5":1.0,"Tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","SOH":92.5}}]}'.lower
E        +      where '{"detail":[{"type":"missing","loc":["body","records"],"msg":"Field required","input":{"IR":0.0085,"QCharge":1.065,"Tavg":30.2,"Tmax":32.5,"Tmin":28.0,"chargetime":40.5,"cycle":120.0,"IR_is_zero":0.0,"temp_sensor_fault":0.0,"IR_lag1":0.0084,"IR_delta":0.0001,"QCharge_lag1":1.066,"QCharge_delta":-0.001,"Tavg_lag1":30.1,"Tavg_delta":0.1,"chargetime_lag1":40.6,"chargetime_delta":-0.1,"IR_accel":1.0,"QCharge_accel":1.0,"Tavg_accel":1.0,"chargetime_accel":1.0,"thermal_dissipation_rate":1.0,"charge_efficiency_proxy":1.0,"resistance_growth_ratio":1.0,"IR_roll_mean_5":1.0,"IR_roll_std_5":1.0,"QCharge_roll_mean_5":1.0,"QCharge_roll_std_5":1.0,"Tavg_roll_mean_5":1.0,"Tavg_roll_std_5":1.0,"cum_capacity_fade_rate":0.00025,"cum_resistance_growth_rate":4e-05,"battery_id":42,"row_id":"test_cell_042","SOH":92.5}}]}' =<Response [422 Unprocessable Entity]>.text

tests\test_api_integration.py:150: AssertionError
_____________________ test_10_invalid_physical_value ______________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_10_invalid_physical_value(valid_cycle_payload):
        bad_payload = valid_cycle_payload.copy()
        bad_payload["cycle"] = 0.0  # cycle must be >= 1
        resp = client.post("/predict", json=bad_payload)
>       assert resp.status_code == 400
E       assert 422 == 400
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests\test_api_integration.py:158: AssertionError
________________ test_11_deterministic_repeated_prediction ________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_11_deterministic_repeated_prediction(valid_cycle_payload):
        resp1 = client.post("/predict", json=valid_cycle_payload)
        resp2 = client.post("/predict", json=valid_cycle_payload)
>       assert resp1.status_code == 200 and resp2.status_code == 200
E       assert (422 == 200)
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests\test_api_integration.py:166: AssertionError
______________________ test_13_metadata_preservation ______________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_13_metadata_preservation(valid_cycle_payload):
        resp = client.post("/predict", json=valid_cycle_payload)
>       assert resp.status_code == 200
E       assert 422 == 200
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests\test_api_integration.py:192: AssertionError
___________________ test_14_raw_prediction_preservation ___________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_14_raw_prediction_preservation(valid_cycle_payload):
        resp = client.post("/predict", json=valid_cycle_payload)
>       assert resp.status_code == 200
E       assert 422 == 200
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests\test_api_integration.py:201: AssertionError
________________________ test_15_display_bounding _________________________

valid_cycle_payload = {'IR': 0.0085, 'QCharge': 1.065, 'Tavg': 30.2, 'Tmax': 32.5, ...}

    def test_15_display_bounding(valid_cycle_payload):
        resp = client.post("/predict", json=valid_cycle_payload)
>       assert resp.status_code == 200
E       assert 422 == 200
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests\test_api_integration.py:213: AssertionError
============================ warnings summary =============================
C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
========================= short test summary info =========================
FAILED tests/test_api_integration.py::test_03_valid_prediction - assert 422== 200
FAILED tests/test_api_integration.py::test_07_qdischarge_leakage_rejection - assert 'leakage' in '{"detail":[{"type":"missing","loc":["body","record...
FAILED tests/test_api_integration.py::test_08_max_cycle_leakage_rejection -assert 'leakage' in '{"detail":[{"type":"missing","loc":["body","record...
FAILED tests/test_api_integration.py::test_09_cross_target_leakage_rejection - assert 'leakage' in '{"detail":[{"type":"missing","loc":["body","record...
FAILED tests/test_api_integration.py::test_10_invalid_physical_value - assert 422 == 400
FAILED tests/test_api_integration.py::test_11_deterministic_repeated_prediction - assert (422 == 200)
FAILED tests/test_api_integration.py::test_13_metadata_preservation - assert 422 == 200
FAILED tests/test_api_integration.py::test_14_raw_prediction_preservation -assert 422 == 200
FAILED tests/test_api_integration.py::test_15_display_bounding - assert 422== 200
================= 9 failed, 9 passed, 1 warning in 6.91s ==================
=========================== test session starts ===========================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 21 items                                                         

tests/test_decision_engine.py::test_soh_regime_classification PASSED [  4%]
tests/test_decision_engine.py::test_rul_regime_classification PASSED [  9%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[95.0-900.0-95.0-900.0-PRIMARY_OPERATION-CONTINUED_PRIMARY_OPERATION-STRONG-HEALTHY_NORMAL_AGING-EARLY_LIFE] PASSED [ 14%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[92.0-550.0-92.0-550.0-PRIMARY_OPERATION-CONTINUED_PRIMARY_OPERATION-MODERATE-HEALTHY_NORMAL_AGING-MID_LIFE] PASSED [ 19%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[91.0-150.0-91.0-150.0-SECOND_LIFE_CANDIDATE-LIGHT_DUTY_STATIONARY_STORAGE-REVIEW_REQUIRED-HEALTHY_NORMAL_AGING-NEAR_END_OF_LIFE] PASSED [ 23%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[85.0-850.0-85.0-850.0-SECOND_LIFE_CANDIDATE-STATIONARY_ENERGY_STORAGE-STRONG-DEGRADED_SECOND_LIFE_CANDIDATE-EARLY_LIFE] PASSED [ 28%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[84.0-600.0-84.0-600.0-SECOND_LIFE_CANDIDATE-STATIONARY_ENERGY_STORAGE-STRONG-DEGRADED_SECOND_LIFE_CANDIDATE-MID_LIFE] PASSED [ 33%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[84.0-400.0-84.0-400.0-SECOND_LIFE_CANDIDATE-STATIONARY_ENERGY_STORAGE-MODERATE-DEGRADED_SECOND_LIFE_CANDIDATE-MID_LIFE] PASSED [ 38%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[82.0-200.0-82.0-200.0-SECOND_LIFE_CANDIDATE-LIGHT_DUTY_STATIONARY_STORAGE-REVIEW_REQUIRED-DEGRADED_SECOND_LIFE_CANDIDATE-NEAR_END_OF_LIFE] PASSED [ 42%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[75.0-850.0-75.0-850.0-SECOND_LIFE_CANDIDATE-STATIONARY_ENERGY_STORAGE-REVIEW_REQUIRED-CRITICAL_KNEE_PRIMARY_RETIREMENT-EARLY_LIFE] PASSED [ 47%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[76.0-450.0-76.0-450.0-SECOND_LIFE_CANDIDATE-STATIONARY_ENERGY_STORAGE-REVIEW_REQUIRED-CRITICAL_KNEE_PRIMARY_RETIREMENT-MID_LIFE] PASSED [ 52%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[72.0-120.0-72.0-120.0-MATERIAL_RECYCLING-DIRECT_MATERIAL_RECOVERY-STRONG-CRITICAL_KNEE_PRIMARY_RETIREMENT-NEAR_END_OF_LIFE] PASSED [ 57%]
tests/test_decision_engine.py::test_all_decision_matrix_combinations[68.0--30.48-68.0-0.0-MATERIAL_RECYCLING-DIRECT_MATERIAL_RECOVERY-STRONG-CRITICAL_KNEE_PRIMARY_RETIREMENT-NEAR_END_OF_LIFE] PASSED [ 61%]
tests/test_decision_engine.py::test_soh_boundary_90 PASSED           [ 66%]
tests/test_decision_engine.py::test_soh_boundary_80 PASSED           [ 71%]
tests/test_decision_engine.py::test_rul_boundary_800 PASSED          [ 76%]
tests/test_decision_engine.py::test_rul_boundary_300 PASSED          [ 80%]
tests/test_decision_engine.py::test_extreme_values PASSED            [ 85%]
tests/test_decision_engine.py::test_decision_engine_determinism PASSED [ 90%]
tests/test_decision_engine.py::test_engine_schema_conformance PASSED [ 95%]
tests/test_decision_engine.py::test_raw_prediction_unclipped_preservation PASSED [100%]

=========================== 21 passed in 1.46s ============================
=========================== test session starts ===========================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 19 items                                                         

tests/test_decision_api.py::test_01_valid_decision_assessment PASSED [  5%]
tests/test_decision_api.py::test_02_response_schema_completeness PASSED [ 10%]
tests/test_decision_api.py::test_03_metadata_preservation PASSED     [ 15%]
tests/test_decision_api.py::test_04_leakage_rejection_qdischarge PASSED [ 21%]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[max_cycle] PASSED [ 26%]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[final_cycle] PASSED [ 31%]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[terminal_cycle] PASSED [ 36%]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[total_cycles] PASSED [ 42%]
tests/test_decision_api.py::test_06_leakage_rejection_cross_target[SOH] PASSED [ 47%]
tests/test_decision_api.py::test_06_leakage_rejection_cross_target[RUL] PASSED [ 52%]
tests/test_decision_api.py::test_07_missing_feature_rejection PASSED [ 57%]
tests/test_decision_api.py::test_08_nan_feature_rejection PASSED     [ 63%]
tests/test_decision_api.py::test_09_inf_feature_rejection PASSED     [ 68%]
tests/test_decision_api.py::test_10_physical_bounds_cycle PASSED     [ 73%]
tests/test_decision_api.py::test_11_physical_bounds_negative_qcharge PASSED[ 78%]
tests/test_decision_api.py::test_12_deterministic_repeated_calls PASSED [ 84%]
tests/test_decision_api.py::test_13_raw_and_display_predictions PASSED [ 89%]
tests/test_decision_api.py::test_14_disclaimer_presence PASSED       [ 94%]
tests/test_decision_api.py::test_15_root_endpoint_includes_decision_route PASSED [100%]

============================ warnings summary =============================
C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_decision_api.py::test_04_leakage_rejection_qdischarge
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[max_cycle]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[final_cycle]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[terminal_cycle]
tests/test_decision_api.py::test_05_leakage_rejection_cycle_horizons[total_cycles]
tests/test_decision_api.py::test_06_leakage_rejection_cross_target[SOH]
tests/test_decision_api.py::test_06_leakage_rejection_cross_target[RUL]
  C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\Lib\site-packages\anyio\_backends\_asyncio.py:1002: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    result = context.run(func, *args)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
===================== 19 passed, 8 warnings in 6.39s ======================
PS D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI> 
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
soh_base_path = BASE_DIR / "ml" / "artifacts" / "models" / "task_2l" / "soh_hist_gradient_boosting.joblib"
rul_base_path = BASE_DIR / "ml" / "artifacts" / "models" / "task_2l" / "rul_hist_gradient_boosting.joblib"
assert os.path.exists(soh_base_path), f"Baseline model missing: {soh_base_path}"
assert os.path.exists(rul_base_path), f"Baseline model missing: {rul_base_path}"
print("  [PASS] Baseline model files and benchmarks preserved intact.")

# 9. Config JSON File Alignment
print("[CHECK 9] Validating reports/modeling/task_2m_1_config.json...")
config_path = BASE_DIR / "reports" / "modeling" / "task_2m_1_config.json"
assert os.path.exists(config_path), f"Missing config file: {config_path}"
with open(config_path, "r") as f:
    cfg = json.load(f)
assert cfg["raw_dataset_hash"] == EXPECTED_RAW_SHA256
assert cfg["models_trained"] is False, "models_trained must be False in Task 2M.1"
assert cfg["partitions"]["test"]["status"] == "STRICTLY_QUARANTINED"
print("  [PASS] Machine-readable config JSON verified.")

# 10. Design Markdown Report Alignment
print("[CHECK 10] Validating reports/modeling/task_2m_1_advanced_model_design.md...")
report_path = BASE_DIR / "reports" / "modeling" / "task_2m_1_advanced_model_design.md"
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
