"""
EcoCycle AI — Integration Test Suite for Second-Life Decision API
Task 2O — Second-Life Decision Engine

Tests for the POST /decision/assess endpoint:
1. Valid decision assessment (HTTP 200)
2. Response schema completeness (decision, predictions, regimes, reasoning, rules, provenance, disclaimer)
3. Metadata preservation (battery_id, row_id)
4. Anti-leakage rejection: QDischarge (HTTP 422)
5. Anti-leakage rejection: max_cycle, final_cycle, terminal_cycle, total_cycles (HTTP 422)
6. Anti-leakage rejection: cross-target SOH, RUL (HTTP 422)
7. Missing feature rejection (HTTP 422)
8. Null / NaN feature rejection (HTTP 400 or 422)
9. Inf feature rejection (HTTP 400 or 422)
10. Physical bounds violation: cycle <= 0 (HTTP 400)
11. Physical bounds violation: negative QCharge (HTTP 400)
12. Deterministic repeated API calls
13. Unclipped raw prediction and bounded display preservation
14. Non-certification disclaimer presence
15. End-to-end root & health endpoint verification
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.api.main import app
from src.models.feature_schema import ADVANCED_FEATURE_COLUMNS

client = TestClient(app)


@pytest.fixture
def valid_telemetry_payload():
    """Generates a valid 32-feature battery cycle record with metadata."""
    payload = {col: 1.0 for col in ADVANCED_FEATURE_COLUMNS}
    payload["cycle"] = 120.0
    payload["IR"] = 0.0085
    payload["QCharge"] = 1.065
    payload["Tavg"] = 30.2
    payload["Tmax"] = 32.5
    payload["Tmin"] = 28.0
    payload["chargetime"] = 40.5
    payload["IR_is_zero"] = 0.0
    payload["temp_sensor_fault"] = 0.0
    payload["IR_lag1"] = 0.0084
    payload["IR_delta"] = 0.0001
    payload["QCharge_lag1"] = 1.066
    payload["QCharge_delta"] = -0.001
    payload["Tavg_lag1"] = 30.1
    payload["Tavg_delta"] = 0.1
    payload["chargetime_lag1"] = 40.6
    payload["chargetime_delta"] = -0.1
    payload["cum_capacity_fade_rate"] = 0.00025
    payload["cum_resistance_growth_rate"] = 0.00004
    payload["battery_id"] = 42
    payload["row_id"] = "cell_42_cycle_120"
    return payload


# 1. Valid decision assessment (HTTP 200)
def test_01_valid_decision_assessment(valid_telemetry_payload):
    resp = client.post("/decision/assess", json=valid_telemetry_payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"
    assert "decision" in data
    assert "predictions" in data
    assert "regimes" in data
    assert "reasoning" in data
    assert "rules" in data
    assert "provenance" in data
    assert "disclaimer" in data


# 2. Response schema completeness
def test_02_response_schema_completeness(valid_telemetry_payload):
    resp = client.post("/decision/assess", json=valid_telemetry_payload)
    assert resp.status_code == 200
    data = resp.json()

    # Decision detail
    dec = data["decision"]
    assert dec["category"] in ["PRIMARY_OPERATION", "SECOND_LIFE_CANDIDATE", "MATERIAL_RECYCLING"]
    assert dec["recommended_application"] in [
        "CONTINUED_PRIMARY_OPERATION",
        "STATIONARY_ENERGY_STORAGE",
        "LIGHT_DUTY_STATIONARY_STORAGE",
        "DIRECT_MATERIAL_RECOVERY"
    ]
    assert dec["decision_strength"] in ["STRONG", "MODERATE", "REVIEW_REQUIRED"]

    # Predictions
    preds = data["predictions"]
    assert "soh" in preds and "rul" in preds
    assert isinstance(preds["soh"]["raw"], float)
    assert isinstance(preds["soh"]["display"], float)
    assert preds["soh"]["units"] == "%"
    assert isinstance(preds["rul"]["raw"], float)
    assert isinstance(preds["rul"]["display"], float)
    assert preds["rul"]["units"] == "cycles"

    # Regimes
    regimes = data["regimes"]
    assert "soh" in regimes and "rul" in regimes
    assert regimes["soh"] in [
        "HEALTHY_NORMAL_AGING",
        "DEGRADED_SECOND_LIFE_CANDIDATE",
        "CRITICAL_KNEE_PRIMARY_RETIREMENT"
    ]
    assert regimes["rul"] in [
        "EARLY_LIFE",
        "MID_LIFE",
        "NEAR_END_OF_LIFE"
    ]

    # Reasoning steps
    assert isinstance(data["reasoning"], list)
    assert len(data["reasoning"]) >= 3

    # Rules applied
    rules = data["rules"]
    assert "soh_thresholds" in rules
    assert "rul_thresholds" in rules
    assert rules["soh_thresholds"]["healthy_normal_aging"] == ">=90.0%"
    assert rules["soh_thresholds"]["degraded_second_life"] == "80.0% - 90.0%"
    assert rules["soh_thresholds"]["critical_knee_retirement"] == "<80.0%"

    # Provenance
    prov = data["provenance"]
    assert prov["soh_model_id"] == "soh_xgboost_32f"
    assert prov["rul_model_id"] == "rul_catboost_32f"
    assert prov["pipeline_version"] == "1.0.0"
    assert prov["decision_engine"] == "task_2o_v1"

    # Disclaimer
    assert "safety certification" in data["disclaimer"]


# 3. Metadata preservation
def test_03_metadata_preservation(valid_telemetry_payload):
    resp = client.post("/decision/assess", json=valid_telemetry_payload)
    assert resp.status_code == 200
    meta = resp.json()["metadata"]
    assert meta["battery_id"] == 42
    assert meta["row_id"] == "cell_42_cycle_120"


# 4. Anti-leakage rejection: QDischarge
def test_04_leakage_rejection_qdischarge(valid_telemetry_payload):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload["QDischarge"] = 1.05
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code == 422
    assert "leakage" in resp.text.lower()


# 5. Anti-leakage rejection: lifecycle target & horizon columns
@pytest.mark.parametrize("leakage_key", ["max_cycle", "final_cycle", "terminal_cycle", "total_cycles"])
def test_05_leakage_rejection_cycle_horizons(valid_telemetry_payload, leakage_key):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload[leakage_key] = 1200
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code == 422
    assert "leakage" in resp.text.lower()


# 6. Anti-leakage rejection: cross-target SOH, RUL
@pytest.mark.parametrize("cross_target", ["SOH", "RUL"])
def test_06_leakage_rejection_cross_target(valid_telemetry_payload, cross_target):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload[cross_target] = 85.0
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code == 422
    assert "leakage" in resp.text.lower()


# 7. Missing feature rejection
def test_07_missing_feature_rejection(valid_telemetry_payload):
    bad_payload = valid_telemetry_payload.copy()
    del bad_payload["IR_delta"]
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code in [400, 422]


# 8. Null / NaN feature rejection
def test_08_nan_feature_rejection(valid_telemetry_payload):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload["QCharge_roll_mean_5"] = None
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code in [400, 422]


# 9. Inf feature rejection
def test_09_inf_feature_rejection(valid_telemetry_payload):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload["thermal_dissipation_rate"] = "Infinity"
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code in [400, 422]


# 10. Physical bounds violation: cycle <= 0
def test_10_physical_bounds_cycle(valid_telemetry_payload):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload["cycle"] = 0.0
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code == 400
    assert "physical bound" in resp.text.lower()


# 11. Physical bounds violation: negative QCharge
def test_11_physical_bounds_negative_qcharge(valid_telemetry_payload):
    bad_payload = valid_telemetry_payload.copy()
    bad_payload["QCharge"] = -0.5
    resp = client.post("/decision/assess", json=bad_payload)
    assert resp.status_code == 400
    assert "physical bound" in resp.text.lower()


# 12. Deterministic repeated API calls
def test_12_deterministic_repeated_calls(valid_telemetry_payload):
    responses = [client.post("/decision/assess", json=valid_telemetry_payload).json() for _ in range(5)]
    first = responses[0]
    for r in responses[1:]:
        assert r["decision"] == first["decision"]
        assert r["predictions"] == first["predictions"]
        assert r["regimes"] == first["regimes"]
        assert r["reasoning"] == first["reasoning"]


# 13. Unclipped raw prediction and bounded display preservation
def test_13_raw_and_display_predictions(valid_telemetry_payload):
    resp = client.post("/decision/assess", json=valid_telemetry_payload)
    assert resp.status_code == 200
    preds = resp.json()["predictions"]
    assert "raw" in preds["soh"] and "display" in preds["soh"]
    assert "raw" in preds["rul"] and "display" in preds["rul"]
    assert 0.0 <= preds["soh"]["display"] <= 100.0
    assert preds["rul"]["display"] >= 0.0


# 14. Non-certification disclaimer presence
def test_14_disclaimer_presence(valid_telemetry_payload):
    resp = client.post("/decision/assess", json=valid_telemetry_payload)
    assert resp.status_code == 200
    disclaimer = resp.json()["disclaimer"]
    assert "decision-support assessment" in disclaimer
    assert "not a battery safety certification" in disclaimer


# 15. Root endpoint documentation link verification
def test_15_root_endpoint_includes_decision_route():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "inference_endpoints" in data
    assert "decision_assessment" in data["inference_endpoints"]
    assert data["inference_endpoints"]["decision_assessment"] == "POST /decision/assess"
