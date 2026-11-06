"""
Unit Tests for Final Model Loading & Registry Verification
Task 2M.4 — Final Model Packaging & Inference Pipeline
"""

import os
import pytest
import tempfile
import json
from ml.models.final_registry import (
    FinalModelRegistry,
    ModelRegistryError,
    get_default_registry
)


def test_registry_initialization():
    """Verify default registry loads successfully and passes initial integrity."""
    reg = get_default_registry()
    assert reg is not None
    assert "models" in reg.registry_data
    assert "soh" in reg.registry_data["models"]
    assert "rul" in reg.registry_data["models"]


def test_soh_model_loading():
    """Verify SOH XGBoost 32f model loads cleanly and matches metadata."""
    reg = get_default_registry()
    soh_model = reg.load_model("soh")
    assert soh_model is not None
    assert hasattr(soh_model, "predict")
    assert soh_model.n_features_in_ == 32

    meta = reg.get_model_metadata("soh")
    assert meta["model_id"] == "soh_xgboost_32f"
    assert meta["feature_count"] == 32
    assert meta["framework"] == "xgboost"


def test_rul_model_loading():
    """Verify RUL CatBoost 32f model loads cleanly and matches metadata."""
    reg = get_default_registry()
    rul_model = reg.load_model("rul")
    assert rul_model is not None
    assert len(rul_model.feature_names_) == 32

    meta = reg.get_model_metadata("rul")
    assert meta["model_id"] == "rul_catboost_32f"
    assert meta["feature_count"] == 32
    assert meta["framework"] == "catboost"


def test_registry_caching():
    """Verify model instances are cached on repeated load calls."""
    reg = get_default_registry()
    m1 = reg.load_model("soh")
    m2 = reg.load_model("soh")
    assert m1 is m2


def test_unknown_target_raises_error():
    """Verify loading unknown target raises ValueError."""
    reg = get_default_registry()
    with pytest.raises(ValueError, match="Unknown target"):
        reg.load_model("nonexistent_target")


def test_fail_fast_on_missing_config():
    """Verify fail-fast behavior when registry configuration file is missing."""
    with pytest.raises(ModelRegistryError, match="Registry configuration file missing"):
        FinalModelRegistry(config_path="nonexistent_config_path.json")


def test_fail_fast_on_corrupted_config():
    """Verify fail-fast behavior when registry config has missing fields."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump({"invalid": "schema"}, f)
        temp_path = f.name

    try:
        with pytest.raises(ModelRegistryError, match="missing required 'models' section"):
            FinalModelRegistry(config_path=temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_fail_fast_on_hash_mismatch():
    """Verify fail-fast behavior when artifact hash is tampered or mismatched."""
    reg = get_default_registry()
    fake_config = {
        "project": "EcoCycle AI",
        "models": {
            "soh": {
                "artifact_path": reg.registry_data["models"]["soh"]["artifact_path"],
                "artifact_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
            },
            "rul": reg.registry_data["models"]["rul"]
        }
    }

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(fake_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ModelRegistryError, match="Artifact hash mismatch"):
            FinalModelRegistry(config_path=temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
