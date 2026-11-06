"""
Unit Tests for Input Validation & Anti-Leakage Safeguards
Task 2M.4 — Final Model Packaging & Inference Pipeline
"""

import pytest
import numpy as np
import pandas as pd
from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
from ml.models.input_validation import (
    validate_inference_input,
    InputValidationError,
    DataLeakageError
)


@pytest.fixture
def valid_32_feature_dict():
    """Generates a physically valid dictionary containing all 32 causal features."""
    sample = {col: 1.0 for col in ADVANCED_FEATURE_COLUMNS}
    sample["cycle"] = 50.0
    sample["IR"] = 0.05
    sample["QCharge"] = 1.08
    sample["Tavg"] = 25.0
    sample["Tmax"] = 28.0
    sample["Tmin"] = 22.0
    sample["chargetime"] = 45.0
    sample["IR_is_zero"] = 0.0
    sample["temp_sensor_fault"] = 0.0
    sample["cum_capacity_fade_rate"] = 0.0005
    sample["cum_resistance_growth_rate"] = 0.0001
    return sample


def test_valid_input_dict(valid_32_feature_dict):
    """Verify clean dictionary passes validation and yields 32 features."""
    X, meta = validate_inference_input(valid_32_feature_dict)
    assert isinstance(X, pd.DataFrame)
    assert X.shape == (1, 32)
    assert list(X.columns) == ADVANCED_FEATURE_COLUMNS
    assert X.dtypes.iloc[0] == np.float64


def test_valid_input_dataframe(valid_32_feature_dict):
    """Verify clean DataFrame passes validation."""
    df = pd.DataFrame([valid_32_feature_dict, valid_32_feature_dict])
    X, meta = validate_inference_input(df)
    assert X.shape == (2, 32)
    assert list(X.columns) == ADVANCED_FEATURE_COLUMNS


def test_deterministic_column_ordering(valid_32_feature_dict):
    """Verify arbitrary input column order is deterministically sorted to canonical schema."""
    # Reverse key order
    shuffled_dict = {k: valid_32_feature_dict[k] for k in reversed(list(valid_32_feature_dict.keys()))}
    X, _ = validate_inference_input(shuffled_dict)
    assert list(X.columns) == ADVANCED_FEATURE_COLUMNS


def test_metadata_segregation(valid_32_feature_dict):
    """Verify non-predictive metadata (battery_id, row_id) is excluded from X."""
    data = valid_32_feature_dict.copy()
    data["battery_id"] = 42
    data["row_id"] = 1001

    X, meta = validate_inference_input(data)
    assert "battery_id" not in X.columns
    assert "row_id" not in X.columns
    assert "battery_id" in meta.columns
    assert "row_id" in meta.columns
    assert X.shape == (1, 32)


def test_missing_features_raise_error(valid_32_feature_dict):
    """Verify omission of any causal feature raises InputValidationError."""
    incomplete = valid_32_feature_dict.copy()
    del incomplete["QCharge_lag1"]
    del incomplete["cum_capacity_fade_rate"]

    with pytest.raises(InputValidationError, match="missing 2 required causal feature"):
        validate_inference_input(incomplete)


def test_nan_features_raise_error(valid_32_feature_dict):
    """Verify presence of NaN raises InputValidationError."""
    corrupt = valid_32_feature_dict.copy()
    corrupt["IR_roll_mean_5"] = np.nan

    with pytest.raises(InputValidationError, match="Input features contain NaN values"):
        validate_inference_input(corrupt)


def test_inf_features_raise_error(valid_32_feature_dict):
    """Verify presence of Infinite values raises InputValidationError."""
    corrupt = valid_32_feature_dict.copy()
    corrupt["thermal_dissipation_rate"] = np.inf

    with pytest.raises(InputValidationError, match="Input features contain infinite values"):
        validate_inference_input(corrupt)


def test_leakage_qdischarge_rejected(valid_32_feature_dict):
    """Verify QDischarge leakage column is rejected with DataLeakageError."""
    leak = valid_32_feature_dict.copy()
    leak["QDischarge"] = 1.05

    with pytest.raises(DataLeakageError, match="Forbidden column 'QDischarge'"):
        validate_inference_input(leak)


def test_leakage_max_cycle_rejected(valid_32_feature_dict):
    """Verify future max_cycle column is rejected with DataLeakageError."""
    leak = valid_32_feature_dict.copy()
    leak["max_cycle"] = 1200

    with pytest.raises(DataLeakageError, match="Forbidden column 'max_cycle'"):
        validate_inference_input(leak)


def test_cross_target_soh_in_rul_rejected(valid_32_feature_dict):
    """Verify SOH ground truth in RUL input is rejected."""
    leak = valid_32_feature_dict.copy()
    leak["SOH"] = 85.0

    with pytest.raises(DataLeakageError, match="Cross-target leakage detected! Ground-truth 'SOH'"):
        validate_inference_input(leak, target="rul")


def test_cross_target_rul_in_soh_rejected(valid_32_feature_dict):
    """Verify RUL ground truth in SOH input is rejected."""
    leak = valid_32_feature_dict.copy()
    leak["RUL"] = 300.0

    with pytest.raises(DataLeakageError, match="Cross-target leakage detected! Ground-truth 'RUL'"):
        validate_inference_input(leak, target="soh")


def test_physical_bounds_cycle(valid_32_feature_dict):
    """Verify cycle < 1 is rejected."""
    corrupt = valid_32_feature_dict.copy()
    corrupt["cycle"] = 0.0

    with pytest.raises(InputValidationError, match="Physical bound violation for feature 'cycle'"):
        validate_inference_input(corrupt)


def test_physical_bounds_negative_qcharge(valid_32_feature_dict):
    """Verify negative QCharge is rejected."""
    corrupt = valid_32_feature_dict.copy()
    corrupt["QCharge"] = -0.1

    with pytest.raises(InputValidationError, match="Physical bound violation for feature 'QCharge'"):
        validate_inference_input(corrupt)
