"""Evidence, grouped evaluation, missing-history and API regression tests.

Small constructed fixtures test code only; never enter measured evaluation.
"""
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.pipeline_v3 import get_bundle
from ml.pipeline_v3.inference import ModelBundle
from ml.pipeline_v3.preprocessing import RAW, DOMAIN, MeasurementPreprocessor
from ml.pipeline_v3.train import grouped_protocol_splits, life_trajectories, metric_report
from scripts.build_measured_extension import validate_discharge_labels
from scripts.fetch_wheeler_characterizations import extract_measurements

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "ml/artifacts/pipeline_v3/run-20261111-measured-v3.0.0"


def test_discharge_reference_never_charge_or_degraded_start():
    data = pd.DataFrame(dict(battery_id=["A", "A"], cycle=[0, 400], QDischarge=[1., .6],
        QCharge=[1.02, .62], reference_capacity_Ah=[1., 1.], reference_cycle=[0, 0], SOH=[100., 60.]))
    validate_discharge_labels(data)
    with pytest.raises(ValueError, match="cycle-0"):
        validate_discharge_labels(data.iloc[1:])
    with pytest.raises(ValueError, match="discharge/reference"):
        validate_discharge_labels(data.assign(SOH=[100, 62]))
    with pytest.raises(ValueError, match="never charge"):
        validate_discharge_labels(data.assign(reference_capacity_Ah=1.02))
    with pytest.raises(ValueError, match="Duplicate"):
        validate_discharge_labels(pd.concat([data, data]))


def test_raw_step_time_order_and_separate_capacity_units():
    # File order is shuffled, as in publisher CSV blocks. Step time is seconds.
    raw = pd.DataFrame(dict(Step_Index=[11, 13, 11, 13], Step_Time=[3600, 7200, 1, 1],
        Current=[-.367, .36, -.367, .36], Voltage=[2.499, 3.65, 3.55, 2.9],
        Charge_Capacity=[0, 1.02, 0, 0], Discharge_Capacity=[1, 1, 0, 1]))
    result = extract_measurements(raw.to_csv(sep=";", index=False).encode())
    assert result["status"] == "ok"
    assert result["QDischarge"] == 1 and result["QCharge"] == 1.02
    assert result["chargetime"] == 120
    assert result["discharge_voltage_end_V"] == 2.499


def test_grouped_protocol_partition_order_independence():
    data = pd.DataFrame(dict(battery_id=["A", "B", "C", "D", "E", "F"], test_group=[1, 1, 1, 2, 2, 2]))
    split = grouped_protocol_splits(data)
    assert split == grouped_protocol_splits(data.sample(frac=1, random_state=9))
    groups = [set(ids) for ids in split.values()]
    assert all(groups[i].isdisjoint(groups[j]) for i in range(3) for j in range(i))
    assert set.union(*groups) == set(data.battery_id)


def test_no_guessed_history_or_discharge_features():
    raw = pd.DataFrame(dict(battery_id=["A"] * 3, cycle=[800, 1200, 1600], QCharge=[.8, .7, .6], chargetime=[130, 115, 100]))
    preprocessor = MeasurementPreprocessor().fit(raw)
    support = dict(preprocessor.support)
    features = preprocessor.transform(raw, "history")
    assert features.iloc[0].filter(like="lag1").isna().all()
    assert features.iloc[0].filter(like="past_mean5").isna().all()
    assert features.iloc[1].QCharge_delta_per_cycle == pytest.approx(-.1 / 400)
    altered = raw.copy()
    altered.loc[2, "QCharge"] = 1.8
    pd.testing.assert_frame_equal(features.iloc[:2], preprocessor.transform(altered, "history").iloc[:2])
    assert preprocessor.support == support
    with pytest.raises(ValueError, match="leakage"):
        preprocessor.transform(raw.assign(QDischarge=.5))


def test_sub80_does_not_become_second_life_failure():
    raw = pd.DataFrame(dict(battery_id=["A"] * 3 + ["B"] * 2, cycle=[0, 400, 800, 800, 1200], SOH=[100, 75, 55, 65, 50]))
    trajectories = life_trajectories(raw).set_index("battery_id")
    assert trajectories.loc["A", "primary_life_crossing_status"] == "interval_censored"
    assert trajectories.loc["B", "primary_life_crossing_status"] == "left_censored"
    assert not trajectories.second_life_event_observed.any()
    assert trajectories.second_life_rul.isna().all()
    assert trajectories.second_life_endpoint_soh.isna().all()


def test_range_metrics_no_fabricated_support():
    data = pd.DataFrame(dict(battery_id=["A", "B"], cycle=[400, 800], SOH=[55., 65.]))
    metrics, _ = metric_report(data, [57., 62.])
    assert metrics["overall"]["mae"] == 2.5
    assert metrics["by_soh_range"]["[50,60)"]["rmse"] == 2
    assert metrics["by_soh_range"]["[60,70)"]["rmse"] == 3
    assert metrics["by_soh_range"]["[0,50)"]["mae"] is None


@pytest.fixture
def measured_client(monkeypatch):
    if not BUNDLE.exists():
        pytest.skip("Immutable measured bundle not yet trained")
    monkeypatch.setenv("ECOCYCLE_V3_BUNDLE", str(BUNDLE))
    get_bundle.cache_clear()
    with TestClient(app) as client:
        yield client, ModelBundle(BUNDLE)
    get_bundle.cache_clear()


@pytest.mark.parametrize("contract", ["single", "history"])
def test_measured_api_parity_and_unavailable_rul(measured_client, contract):
    client, bundle = measured_client
    measured = pd.read_csv(ROOT / "ml/data/wheeler2025_discharge_measured.csv")
    raw = measured[measured.battery_id == measured.battery_id.iloc[0]][RAW + ["battery_id"]]
    records = raw.iloc[::-1].to_dict("records")
    expected = bundle.predict(records, contract, DOMAIN)
    result = client.post("/v3/predict", json=dict(domain=DOMAIN, contract=contract, records=records))
    assert result.status_code == 200, result.text
    assert result.json() == expected
    assert all(row["rul"] is None for row in expected["results"])


@pytest.mark.parametrize("change", [{"domain": "severson"}, {"SOH": 55}, {"QDischarge": .6}, {"reference_capacity_Ah": 1.1}, {"Tavg": 50}, {"cycle": 1.5}])
def test_v3_refuses_incompatible_or_target_inputs(measured_client, change):
    client, _ = measured_client
    record = dict(QCharge=.7, chargetime=120, cycle=400)
    domain = change.get("domain", DOMAIN)
    record.update({k: v for k, v in change.items() if k != "domain"})
    result = client.post("/v3/predict", json=dict(domain=domain, records=[record]))
    assert result.status_code == 422
