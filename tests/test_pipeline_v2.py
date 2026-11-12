"""Causality, censoring, strict contracts, integrity, and actual API parity."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.pipeline_v2 import get_bundle
from ml.pipeline_v2.inference import ModelBundle
from ml.pipeline_v2.preprocessing import RAW, MeasurementPreprocessor
from ml.pipeline_v2.targets import failure_targets
from ml.preprocessing.split import get_battery_splits

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "ml/artifacts/pipeline_v2/run-20261111-v2.0.1"


@pytest.fixture
def raw():
    return pd.DataFrame([dict(IR=.016 + i * .0001, QCharge=1.07 - i * .001, Tavg=34.,
                              Tmin=31., Tmax=38., chargetime=10.3 + i * .01,
                              cycle=i + 1, battery_id="A") for i in range(8)])


def test_dynamic_group_splits():
    d = pd.DataFrame({"battery_id": np.repeat(np.arange(20), 3)})
    a = get_battery_splits(d)
    assert [len(x) for x in a] == [14, 3, 3]
    assert a == get_battery_splits(d.sample(frac=1, random_state=7))
    assert set(a[0]).isdisjoint(a[1]) and set(a[0]).isdisjoint(a[2])
    assert set().union(*map(set, a)) == set(range(20))
    assert [len(x) for x in get_battery_splits(d[d.battery_id < 3])] == [1, 1, 1]


def test_no_invented_history_or_birth_reference(raw):
    prep = MeasurementPreprocessor().fit(raw)
    partial = raw.iloc[4:]
    x = prep.transform(partial, "history")
    assert x.iloc[0].filter(like="lag1").isna().all()
    assert x.iloc[0].filter(like="past_mean").isna().all()
    assert x.iloc[0].history_count == 0
    assert x.iloc[0].observed_span == 0
    assert x.iloc[1].QCharge_lag1 == partial.QCharge.iloc[0]
    assert not any("initial" in c or "reference" in c or "fade" in c for c in x)


def test_past_only_future_perturbation_and_groups(raw):
    prep = MeasurementPreprocessor().fit(raw)
    x = prep.transform(raw, "history")
    future = raw.copy()
    future.loc[6:, "QCharge"] = 2
    pd.testing.assert_frame_equal(x.iloc[:6], prep.transform(future, "history").iloc[:6])
    other = raw.assign(battery_id="B", IR=.02)
    combined = prep.transform(pd.concat([raw, other], ignore_index=True), "history")
    pd.testing.assert_frame_equal(x, combined.iloc[:8])
    assert combined.iloc[8].IR_lag1 is np.nan or np.isnan(combined.iloc[8].IR_lag1)


def test_sensor_faults_are_reading_based_and_train_only(raw):
    prep = MeasurementPreprocessor().fit(raw)
    parameters = dict(prep.medians)
    broken = raw.copy().assign(battery_id="unseen_faulty_channel")
    broken.loc[0, ["IR", "Tmin", "Tmax", "chargetime"]] = [0, -270, 400, 3934]
    x = prep.transform(broken, "history")
    assert x.iloc[0].IR_is_zero == 1 and x.iloc[0].temp_sensor_fault == 1
    assert x.iloc[0].chargetime_outlier == 1
    assert x.iloc[0].IR == parameters["IR"]
    assert x.iloc[0].Tmax == parameters["Tmax"]
    assert x.iloc[1].IR_lag1 != x.iloc[1].IR_lag1  # no fabricated historical IR
    assert prep.medians == parameters
    healthy_85 = prep.transform(raw.assign(battery_id=85))
    assert not healthy_85.temp_sensor_fault.any()


def test_confirmation_censoring_and_gaps():
    d = pd.DataFrame({"battery_id": [1] * 6 + [2] * 4 + [3] * 4,
                      "cycle": [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 1, 2, 4, 5],
                      "SOH": [90, 79, 81, 79, 78, 77, 90, 89, 88, 79, 79, 79, 79, 79]})
    labeled, trajectories = failure_targets(d)
    assert trajectories.set_index("battery_id").loc[1, "event_cycle"] == 6
    assert labeled[labeled.battery_id == 1].RUL_endpoint.tolist() == [5, 4, 3, 2, 1, 0]
    assert labeled[labeled.battery_id.isin([2, 3])].RUL_endpoint.isna().all()
    assert trajectories.event_observed.sum() == 1
    changed, _ = failure_targets(d, threshold=90, confirmation=1)
    assert changed[changed.battery_id == 1].event_cycle.iloc[0] == 2


def test_duplicate_cycles_rejected(raw):
    prep = MeasurementPreprocessor().fit(raw)
    with pytest.raises(ValueError, match="Duplicate"):
        prep.transform(pd.concat([raw, raw.iloc[[0]]]), "history")


@pytest.fixture(scope="module")
def bundle():
    if not BUNDLE.exists():
        pytest.skip("Run documented training CLI to create the reference bundle.")
    return ModelBundle(BUNDLE)


@pytest.fixture
def client(monkeypatch, bundle):
    monkeypatch.setenv("ECOCYCLE_V2_BUNDLE", str(BUNDLE))
    get_bundle.cache_clear()
    with TestClient(app) as c:
        yield c
    get_bundle.cache_clear()


def test_default_bundle_without_environment_from_another_directory(monkeypatch, tmp_path, bundle, raw):
    monkeypatch.delenv("ECOCYCLE_V2_BUNDLE", raising=False)
    monkeypatch.chdir(tmp_path)
    get_bundle.cache_clear()
    try:
        with TestClient(app) as client:
            health = client.get("/v2/health")
            assert health.status_code == 200, health.text
            assert health.json()["pipeline_version"] == bundle.registry["version"]
            for contract in ["single", "history"]:
                records = raw.iloc[::-1].to_dict("records")
                response = client.post("/v2/predict", json={"contract": contract, "records": records})
                assert response.status_code == 200, response.text
                assert response.json() == bundle.predict(records, contract)
    finally:
        get_bundle.cache_clear()


def test_invalid_explicit_bundle_does_not_use_default(monkeypatch, tmp_path):
    monkeypatch.setenv("ECOCYCLE_V2_BUNDLE", str(tmp_path / "missing-bundle"))
    get_bundle.cache_clear()
    try:
        with TestClient(app) as client:
            for response in [client.get("/v2/health"), client.post("/v2/predict", json={
                "records": [{"QCharge": 1.075, "IR": .016, "cycle": 1}]
            })]:
                assert response.status_code == 503
                assert "Versioned bundle unavailable" in response.json()["detail"]
    finally:
        get_bundle.cache_clear()


@pytest.mark.parametrize("contract", ["single", "history"])
def test_offline_api_exact_parity(client, bundle, raw, contract):
    records = raw.iloc[::-1].to_dict("records")
    expected = bundle.predict(records, contract)
    response = client.post("/v2/predict", json={"records": records, "contract": contract})
    assert response.status_code == 200, response.text
    assert response.json() == expected
    assert expected["results"][0]["rul"] is None if contract == "single" else expected["results"][0]["rul"] is not None


def test_singleton_batch_and_missing_sensors(client):
    result = client.post("/v2/predict", json={"records": [{"QCharge": 1.05, "IR": .016, "cycle": 50}]})
    assert result.status_code == 200
    row = result.json()["results"][0]
    assert row["rul"] is None
    assert row["reliability"]["status"] == "review_required"


def test_metadata_integer_types_preserved(client, bundle, raw):
    records = raw.iloc[:1].assign(battery_id=42, row_id=123).to_dict("records")
    offline = bundle.predict(records)["results"][0]["metadata"]
    assert type(offline["battery_id"]) is int
    assert type(offline["row_id"]) is int
    api = client.post("/v2/predict", json={"records": records}).json()["results"][0]["metadata"]
    assert api == offline and type(api["battery_id"]) is int


@pytest.mark.parametrize("change", [{"IR": -1}, {"QCharge": -1}, {"cycle": 0}, {"QDischarge": 1.0}, {"IR_lag1": .016}, {"SOH": 60}])
def test_v2_rejects_physical_and_leakage_bypasses(client, raw, change):
    record = raw.iloc[0].to_dict() | change
    result = client.post("/v2/predict", json={"records": [record]})
    assert result.status_code == 422, result.text


@pytest.mark.parametrize("mode", ["mixed", "duplicate", "singleton"])
def test_invalid_histories(client, raw, mode):
    records = raw.iloc[:2].to_dict("records")
    if mode == "mixed": records[1]["battery_id"] = "B"
    if mode == "duplicate": records[1]["cycle"] = records[0]["cycle"]
    if mode == "singleton": records = records[:1]
    result = client.post("/v2/predict", json={"contract": "history", "records": records})
    assert result.status_code == 422


def test_low_capacity_extrapolation_is_explicit(client, raw):
    record = raw.iloc[0].to_dict() | {"QCharge": .5}
    result = client.post("/v2/predict", json={"records": [record]}).json()["results"][0]
    assert result["reliability"]["status"] == "review_required"
    assert "QCharge_outside_training_support" in result["reliability"]["warnings"]
    assert any("50-70" in s for s in result["reliability"]["warnings"])


def test_registry_and_artifact_tampering_rejected(tmp_path, bundle):
    # A copied registry can never redirect loading to an unhashed artifact.
    (tmp_path / "registry.json").write_text("{}")
    (tmp_path / "registry.sha256").write_text(bundle.registry_hash)
    with pytest.raises(ValueError, match="Registry hash"):
        ModelBundle(tmp_path)


def test_file_hash_tampering_rejected(tmp_path, bundle):
    import shutil
    for name in ["registry.json", "registry.sha256"]:
        shutil.copyfile(BUNDLE / name, tmp_path / name)
    name = next(iter(bundle.registry["files"]))
    corrupted = tmp_path / name
    corrupted.parent.mkdir(parents=True, exist_ok=True)
    corrupted.write_bytes(b"corrupted artifact")
    with pytest.raises(ValueError, match="Artifact hash mismatch"):
        ModelBundle(tmp_path)


def test_training_never_overwrites_existing_bundle(bundle):
    from types import SimpleNamespace
    from ml.pipeline_v2.train import run
    with pytest.raises(FileExistsError):
        run(SimpleNamespace(output=str(BUNDLE)))


def test_training_feature_matrix_matches_inference(bundle):
    ids = json.loads((BUNDLE / "splits.json").read_text())["test"]
    d = pd.read_csv(ROOT / "ml/data/master_dataset.csv")
    d = d[d.battery_id.isin(ids)]
    x = bundle.preprocessor.transform(d[RAW + ["battery_id"]], "single")
    stored = pd.read_csv(BUNDLE / "single_soh_xgboost_test_predictions.csv")
    np.testing.assert_allclose(bundle.models["single_soh"].predict(x), stored.prediction, rtol=0, atol=1e-12)
    hx = bundle.preprocessor.transform(d[RAW + ["battery_id"]], "history")
    stored_history = pd.read_csv(BUNDLE / "history_soh_xgboost_test_predictions.csv")
    np.testing.assert_allclose(bundle.models["history_soh"].predict(hx[hx.history_count >= 1]), stored_history.prediction, rtol=0, atol=1e-12)


def test_original_data_models_unchanged(bundle):
    from ml.pipeline_v2.inference import digest
    manifest = json.loads((BUNDLE / "original_manifest.json").read_text())
    for name, expected in manifest.items():
        assert digest(ROOT / name) == expected, name


def test_legacy_singleton_batch_and_history_guards():
    from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
    payload = {k: 0. for k in ADVANCED_FEATURE_COLUMNS}
    payload.update(IR=.016, QCharge=1.05, Tmin=31., Tavg=34., Tmax=38., chargetime=10.3, cycle=10., battery_id="A")
    c = TestClient(app)
    batch = c.post("/predict/batch", json={"records": [payload]})
    assert batch.status_code == 200, batch.text
    assert len(batch.json()["results"]) == 1
    history = {k: v for k, v in payload.items() if k in ADVANCED_FEATURE_COLUMNS[:17] + ["battery_id"]}
    assert c.post("/predict", json={"records": [history, history]}).status_code == 400
    assert c.post("/predict", json={"records": [history, history | {"cycle": 11, "battery_id": "B"}]}).status_code == 400
    assert c.post("/predict", json={"records": [history | {"IR": -1}]}).status_code == 400
