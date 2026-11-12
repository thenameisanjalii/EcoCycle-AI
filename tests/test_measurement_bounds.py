"""Dataset provenance and request validation before inference is invoked."""
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes import pipeline_v2
from backend.schemas.measurement_bounds import BOUNDS
from scripts.derive_input_bounds import derive_bounds

ROOT = Path(__file__).resolve().parents[1]
VALID = dict(IR=.016, QCharge=1.075, Tavg=34, Tmax=38, Tmin=31, chargetime=10.3, cycle=1, battery_id="cell-A")


@pytest.fixture
def client(monkeypatch):
    class Bundle:
        calls = []

        def predict(self, records, contract):
            self.calls.append(records)
            return {"records": records}

    bundle = Bundle()
    monkeypatch.setattr(pipeline_v2, "get_bundle", lambda: bundle)
    app = FastAPI()
    app.include_router(pipeline_v2.router)
    with TestClient(app) as client:
        yield client, bundle


def test_bounds_match_the_actual_dataset_and_exclude_sentinels():
    saved = json.loads((ROOT / "configs/prediction_input_bounds.json").read_text(encoding="utf-8"))
    assert derive_bounds() == saved
    assert saved["rows"] == 116663
    assert BOUNDS["IR"]["excluded"] == 4922
    assert BOUNDS["IR"]["min"] > 0
    for field in ["Tmin", "Tavg", "Tmax"]:
        assert BOUNDS[field]["excluded"] == 123
        assert 0 < BOUNDS[field]["min"] < BOUNDS[field]["max"] < 100
    assert BOUNDS["chargetime"]["max"] > 3900


@pytest.mark.parametrize("field", BOUNDS)
def test_numeric_endpoints_and_decimal_strings_are_accepted(client, field):
    client, bundle = client
    for value in [BOUNDS[field]["min"], BOUNDS[field]["max"]]:
        for value in [value, str(value)]:
            response = client.post("/v2/predict", json={"records": [VALID | {field: value}]})
            assert response.status_code == 200, response.text
    assert len(bundle.calls) == 4


@pytest.mark.parametrize("field", BOUNDS)
def test_bad_numeric_values_never_reach_inference(client, field):
    client, bundle = client
    for value in [None, "", "  ", "abc", "NaN", "Infinity", True, False, [], {}, "0x10", "1_000", BOUNDS[field]["min"] - .000001, BOUNDS[field]["max"] + .000001]:
        response = client.post("/v2/predict", json={"records": [VALID | {field: value}]})
        assert response.status_code == 422, response.text
        error = response.json()["detail"][0]
        assert field in error["loc"]
        assert "Allowed range:" in error["msg"]
    record = VALID.copy()
    del record[field]
    response = client.post("/v2/predict", json={"records": [record]})
    assert response.status_code == 422
    assert field in response.json()["detail"][0]["loc"]
    assert not bundle.calls


def test_fractional_cycle_is_rejected(client):
    client, bundle = client
    response = client.post("/v2/predict", json={"records": [VALID | {"cycle": 1.5}]})
    assert response.status_code == 422
    assert "whole number" in response.text
    assert not bundle.calls


@pytest.mark.parametrize("battery_id", [None, "", " \t ", True, False, [], {}, 1.5])
def test_invalid_id_is_rejected(client, battery_id):
    client, bundle = client
    response = client.post("/v2/predict", json={"records": [VALID | {"battery_id": battery_id}]})
    assert response.status_code == 422
    assert "Battery ID" in response.text
    assert not bundle.calls


def test_missing_id_is_rejected(client):
    client, bundle = client
    record = VALID.copy()
    del record["battery_id"]
    assert client.post("/v2/predict", json={"records": [record]}).status_code == 422
    assert not bundle.calls


@pytest.mark.parametrize("battery_id", [0, -1, 10000, "new-cell", "  cell-A  "])
def test_id_is_trimmed_and_not_restricted_to_dataset_ids(client, battery_id):
    client, bundle = client
    response = client.post("/v2/predict", json={"records": [VALID | {"battery_id": battery_id}]})
    assert response.status_code == 200, response.text
    assert bundle.calls[0][0]["battery_id"] == (battery_id.strip() if isinstance(battery_id, str) else battery_id)
