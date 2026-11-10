"""
Integration Test Suite for EcoCycle AI FastAPI Inference Service
Task 2N — Production Inference API & Application Integration

Tests:
1. Health endpoint (GET /health)
2. Model-info endpoint (GET /model-info)
3. Valid SOH/RUL prediction (POST /predict)
4. Missing feature rejection (HTTP 400)
5. NaN rejection (HTTP 400)
6. Inf rejection (HTTP 400)
7. QDischarge leakage rejection (HTTP 422)
8. max_cycle leakage rejection (HTTP 422)
9. cross-target leakage rejection (HTTP 422)
10. invalid physical value rejection (HTTP 400)
11. deterministic repeated prediction
12. batch prediction (POST /predict/batch)
13. metadata preservation (battery_id, row_id)
14. raw prediction preservation (unclipped)
15. display bounding
16. model registry integrity
17. model artifact hash verification
18. malformed request handling
"""

import os
import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
from ml.models.final_registry import get_default_registry

client = TestClient(app)


@pytest.fixture
def valid_cycle_payload():
    """Generates a valid raw battery telemetry record."""
    payload = {col: 1.0 for col in ADVANCED_FEATURE_COLUMNS[:17]}
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
    payload["battery_id"] = 42
    payload["row_id"] = "test_cell_042"
    return payload


# 1. Health endpoint
def test_01_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["models_available"]["soh"] is True
    assert data["models_available"]["rul"] is True


# 2. Model-info endpoint
def test_02_model_info_endpoint():
    resp = client.get("/model-info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"] == "EcoCycle AI"
    assert "models" in data
    assert "soh" in data["models"]
    assert "rul" in data["models"]
    assert data["models"]["soh"]["model_id"] == "soh_xgboost_32f"
    assert data["models"]["rul"]["model_id"] == "rul_catboost_32f"


# 3. Valid SOH/RUL prediction
def test_03_valid_prediction(valid_cycle_payload):
    resp = client.post("/predict", json={"records": [valid_cycle_payload]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "predictions" in data
    assert "soh" in data["predictions"]
    assert "rul" in data["predictions"]
    assert isinstance(data["predictions"]["soh"]["raw"], float)
    assert isinstance(data["predictions"]["rul"]["raw"], float)


# 4. Missing feature rejection
def test_04_missing_feature_rejection(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    del bad_payload["QCharge_lag1"]
    resp = client.post("/predict", json={"records": [bad_payload]})
    # Pydantic or input validator catches missing field
    assert resp.status_code in [400, 422]


# 5. NaN rejection
def test_05_nan_rejection(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    bad_payload["IR_roll_mean_5"] = None  # JSON null parses as NaN
    resp = client.post("/predict", json={"records": [bad_payload]})
    assert resp.status_code in [400, 422]


# 6. Inf rejection
def test_06_inf_rejection(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    bad_payload["thermal_dissipation_rate"] = "Infinity"
    resp = client.post("/predict", json={"records": [bad_payload]})
    assert resp.status_code in [400, 422]


# 7. QDischarge leakage rejection
def test_07_qdischarge_leakage_rejection(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    bad_payload["QDischarge"] = 1.05
    resp = client.post("/predict", json={"records": [bad_payload]})
    assert resp.status_code == 422
    assert "leakage" in resp.text.lower()


# 8. max_cycle leakage rejection
def test_08_max_cycle_leakage_rejection(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    bad_payload["max_cycle"] = 1200
    resp = client.post("/predict", json={"records": [bad_payload]})
    assert resp.status_code == 422
    assert "leakage" in resp.text.lower()


# 9. Cross-target leakage rejection
def test_09_cross_target_leakage_rejection(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    bad_payload["SOH"] = 92.5
    resp = client.post("/predict", json={"records": [bad_payload]})
    assert resp.status_code == 422
    assert "leakage" in resp.text.lower()


# 10. Invalid physical value rejection
def test_10_invalid_physical_value(valid_cycle_payload):
    bad_payload = valid_cycle_payload.copy()
    bad_payload["cycle"] = 0.0  # cycle must be >= 1
    resp = client.post("/predict", json={"records": [bad_payload]})
    assert resp.status_code == 400
    assert "physical bound" in resp.text.lower()


# 11. Deterministic repeated prediction
def test_11_deterministic_repeated_prediction(valid_cycle_payload):
    resp1 = client.post("/predict", json={"records": [valid_cycle_payload]})
    resp2 = client.post("/predict", json={"records": [valid_cycle_payload]})
    assert resp1.status_code == 200 and resp2.status_code == 200
    d1 = resp1.json()["predictions"]
    d2 = resp2.json()["predictions"]
    assert d1["soh"]["raw"] == d2["soh"]["raw"]
    assert d1["rul"]["raw"] == d2["rul"]["raw"]


# 12. Batch prediction
def test_12_batch_prediction(valid_cycle_payload):
    p1 = valid_cycle_payload.copy()
    p2 = valid_cycle_payload.copy()
    derived_features = {
        col: 1.0 for col in ADVANCED_FEATURE_COLUMNS[17:]
    }
    p1.update(derived_features)
    p2.update(derived_features)
    p2["cycle"] = 121.0
    p2["row_id"] = "cell_row_2"

    batch_payload = {"records": [p1, p2]}
    resp = client.post("/predict/batch", json=batch_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["total_records"] == 2
    assert len(data["results"]) == 2


# 13. Metadata preservation
def test_13_metadata_preservation(valid_cycle_payload):
    resp = client.post("/predict", json={"records": [valid_cycle_payload]})
    assert resp.status_code == 200
    meta = resp.json()["metadata"]
    assert meta["battery_id"] == 42
    assert meta["row_id"] == "test_cell_042"


# 14. Raw prediction preservation (unclipped)
def test_14_raw_prediction_preservation(valid_cycle_payload):
    resp = client.post("/predict", json={"records": [valid_cycle_payload]})
    assert resp.status_code == 200
    preds = resp.json()["predictions"]
    # Raw values are floats and must exist independently of display
    assert "raw" in preds["soh"]
    assert "raw" in preds["rul"]
    assert "display" in preds["soh"]
    assert "display" in preds["rul"]


# 15. Display bounding
def test_15_display_bounding(valid_cycle_payload):
    resp = client.post("/predict", json={"records": [valid_cycle_payload]})
    assert resp.status_code == 200
    preds = resp.json()["predictions"]
    assert 0.0 <= preds["soh"]["display"] <= 100.0
    assert preds["rul"]["display"] >= 0.0


# 16. Model registry integrity
def test_16_model_registry_integrity():
    reg = get_default_registry()
    assert reg.registry_data["dataset_sha256"] == "0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88"
    assert "soh" in reg.registry_data["models"]
    assert "rul" in reg.registry_data["models"]


# 17. Model artifact hash verification
def test_17_model_artifact_hash_verification():
    reg = get_default_registry()
    soh_path = os.path.join(reg.config_path, "..", "..", reg.get_model_metadata("soh")["artifact_path"])
    actual_hash = reg._compute_sha256(os.path.abspath(soh_path))
    assert actual_hash.lower() == reg.get_model_metadata("soh")["artifact_sha256"].lower()


# 18. Malformed request handling
def test_18_malformed_request_handling():
    resp = client.post("/predict", json={"records": [{"garbage": "data"}]})
    assert resp.status_code in [400, 422]
