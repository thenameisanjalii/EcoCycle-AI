"""
EcoCycle AI — Centralized Final Model Registry
Task 2M.4 — Final Model Packaging & Inference Pipeline

Loads and verifies:
1. Locked final model registry from configs/final_model_registry.json
2. On-disk binary model artifacts with strict SHA-256 integrity verification
3. Fail-fast error handling if any model artifact, schema, or configuration is missing or tampered
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
import joblib

# Paths
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "configs", "final_model_registry.json")


class ModelRegistryError(Exception):
    """Raised when model registry configuration or physical artifacts fail verification."""
    pass


class FinalModelRegistry:
    """
    Centralized Model Registry Manager for EcoCycle AI.
    Loads and validates locked model binaries and associated metadata.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or CONFIG_PATH
        self.registry_data: Dict[str, Any] = {}
        self._loaded_models: Dict[str, Any] = {}
        self._load_and_verify_registry()

    def _compute_sha256(self, filepath: str) -> str:
        """Computes the SHA-256 hex digest of a file on disk."""
        if not os.path.exists(filepath):
            raise ModelRegistryError(f"Artifact file not found: {filepath}")
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _load_and_verify_registry(self) -> None:
        """Loads registry JSON and verifies all configured artifacts exist and match hashes."""
        if not os.path.exists(self.config_path):
            raise ModelRegistryError(f"Registry configuration file missing: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.registry_data = json.load(f)
        except Exception as e:
            raise ModelRegistryError(f"Failed to parse registry configuration JSON: {e}")

        if "models" not in self.registry_data:
            raise ModelRegistryError("Registry configuration missing required 'models' section.")

        for target in ["soh", "rul"]:
            if target not in self.registry_data["models"]:
                raise ModelRegistryError(f"Registry missing required model target entry: '{target}'")
            
            entry = self.registry_data["models"][target]
            rel_path = entry.get("artifact_path")
            if not rel_path:
                raise ModelRegistryError(f"Registry entry for '{target}' missing 'artifact_path'")

            abs_path = os.path.join(PROJECT_ROOT, rel_path)
            if not os.path.exists(abs_path):
                raise ModelRegistryError(f"Physical model artifact missing on disk: {abs_path}")

            expected_sha256 = entry.get("artifact_sha256")
            if not expected_sha256:
                raise ModelRegistryError(f"Registry entry for '{target}' missing 'artifact_sha256'")

            actual_sha256 = self._compute_sha256(abs_path)
            if actual_sha256.lower() != expected_sha256.lower():
                raise ModelRegistryError(
                    f"Artifact hash mismatch for {target} model ({abs_path})!\n"
                    f"Expected: {expected_sha256}\n"
                    f"Actual:   {actual_sha256}"
                )

    def get_model_metadata(self, target: str) -> Dict[str, Any]:
        """Returns metadata dictionary for a specified target ('soh' or 'rul')."""
        target_key = target.lower().strip()
        if target_key not in self.registry_data["models"]:
            raise ValueError(f"Unknown target '{target}'. Admissible targets: 'soh', 'rul'.")
        return self.registry_data["models"][target_key]

    def load_model(self, target: str) -> Any:
        """
        Loads the trained model estimator instance with caching.
        Performs fail-fast verification of binary integrity.
        """
        target_key = target.lower().strip()
        if target_key in self._loaded_models:
            return self._loaded_models[target_key]

        meta = self.get_model_metadata(target_key)
        abs_path = os.path.join(PROJECT_ROOT, meta["artifact_path"])
        
        # Verify hash again right before loading
        actual_sha256 = self._compute_sha256(abs_path)
        if actual_sha256.lower() != meta["artifact_sha256"].lower():
            raise ModelRegistryError(f"Security error: Artifact {abs_path} was modified before loading!")

        try:
            model = joblib.load(abs_path)
            self._loaded_models[target_key] = model
            return model
        except Exception as e:
            raise ModelRegistryError(f"Failed to load model binary {abs_path}: {e}")

    def get_features(self, target: str) -> list:
        """Returns the exact list of features expected by the model."""
        meta = self.get_model_metadata(target)
        return list(meta["features"])


# Global singleton registry instance
_default_registry: Optional[FinalModelRegistry] = None


def get_default_registry() -> FinalModelRegistry:
    """Returns or initializes the default singleton FinalModelRegistry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = FinalModelRegistry()
    return _default_registry
