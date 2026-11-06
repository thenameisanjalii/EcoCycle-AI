"""
Unit Tests for Inference Contract & Output Specifications
Task 2M.4 — Final Model Packaging & Inference Pipeline
"""

import os
import pytest
import numpy as np
import pandas as pd
from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
from ml.models.inference import (
    predict_soh,
    predict_rul,
    predict_all,
    predict_batch,
    format_presentation_output
)


@pytest.fixture
def sample_features_dict():
    """Generates a realistic single cycle feature record."""
    sample = {col: 0.1 for col in ADVANCED_FEATURE_COLUMNS}
    sample["cycle"] = 150.0
    sample["IR"] = 0.009
    sample["QCharge"] = 1.07
    sample["Tavg"] = 32.5
    sample["Tmax"] = 34.0
    sample["Tmin"] = 31.0
    sample["chargetime"] = 42.0
    sample["IR_is_zero"] = 0.0
    sample["temp_sensor_fault"] = 0.0
    sample["IR_lag1"] = 0.0089
    sample["IR_delta"] = 0.0001
    sample["QCharge_lag1"] = 1.071
    sample["QCharge_delta"] = -0.001
    sample["Tavg_lag1"] = 32.4
    sample["Tavg_delta"] = 0.1
    sample["chargetime_lag1"] = 42.1
    sample["chargetime_delta"] = -0.1
    sample["cum_capacity_fade_rate"] = 0.0002
    sample["cum_resistance_growth_rate"] = 0.00005
    return sample


def test_predict_soh_single_record(sample_features_dict):
    """Verify predict_soh returns a finite float within reasonable range."""
    val = predict_soh(sample_features_dict)
    assert isinstance(val, float)
    assert not np.isnan(val)
    assert not np.isinf(val)
    assert 50.0 <= val <= 105.0


def test_predict_rul_single_record(sample_features_dict):
    """Verify predict_rul returns a finite float."""
    val = predict_rul(sample_features_dict)
    assert isinstance(val, float)
    assert not np.isnan(val)
    assert not np.isinf(val)


def test_predict_all_structure(sample_features_dict):
    """Verify predict_all returns structured dictionary with model versions."""
    res = predict_all(sample_features_dict)
    assert isinstance(res, dict)
    assert "predicted_soh" in res
    assert "predicted_rul" in res
    assert "model_versions" in res
    assert isinstance(res["predicted_soh"], float)
    assert isinstance(res["predicted_rul"], float)
    assert res["model_versions"]["soh_model_id"] == "soh_xgboost_32f"
    assert res["model_versions"]["rul_model_id"] == "rul_catboost_32f"


def test_inference_determinism(sample_features_dict):
    """Verify repeated inference on identical input produces bit-identical output."""
    res1 = predict_all(sample_features_dict)
    res2 = predict_all(sample_features_dict)
    assert res1["predicted_soh"] == res2["predicted_soh"]
    assert res1["predicted_rul"] == res2["predicted_rul"]


def test_batch_inference_preserves_input(sample_features_dict):
    """Verify predict_batch preserves original columns and appends predictions."""
    df_in = pd.DataFrame([sample_features_dict, sample_features_dict])
    df_in["battery_id"] = [10, 10]
    df_in["custom_metadata"] = ["A", "B"]
    
    orig_cols = list(df_in.columns)
    df_out = predict_batch(df_in)

    # Check that original input was not modified in place
    assert "predicted_soh" not in df_in.columns
    assert "predicted_rul" not in df_in.columns

    # Check output
    for col in orig_cols:
        assert col in df_out.columns
    assert "predicted_soh" in df_out.columns
    assert "predicted_rul" in df_out.columns
    assert len(df_out) == 2


def test_raw_prediction_unclipped_preservation():
    """Verify that presentation layer does not alter raw predictions."""
    raw_soh = 103.5
    raw_rul = -15.4

    pres = format_presentation_output(raw_soh, raw_rul)
    # Raw remains strictly unchanged
    assert pres["raw_soh"] == 103.5
    assert pres["raw_rul"] == -15.4

    # Presentation display values are bounded
    assert pres["display_soh"] == 100.0
    assert pres["display_rul"] == 0.0
