"""Hashed, protocol-specific measured SOH bundle; second-life RUL unavailable."""
import importlib.metadata
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.pipeline_v2.inference import digest
from . import VERSION
from .preprocessing import DOMAIN, SINGLE_FEATURES, HISTORY_FEATURES, validate_raw


class ModelBundle:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        registry_path = self.directory / "registry.json"
        self.registry_hash = (self.directory / "registry.sha256").read_text().strip()
        if digest(registry_path) != self.registry_hash:
            raise ValueError("Registry hash mismatch")
        self.registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if self.registry["version"] != VERSION or self.registry["domain"] != DOMAIN:
            raise ValueError("Unsupported measured pipeline or domain")
        for name, expected in self.registry["files"].items():
            path = (self.directory / name).resolve()
            if not path.is_relative_to(self.directory) or digest(path) != expected:
                raise ValueError(f"Artifact hash mismatch: {name}")
        for name in ["__init__.py", "preprocessing.py", "inference.py"]:
            if digest(Path(__file__).parent / name) != digest(self.directory / "source" / name):
                raise ValueError(f"Runtime source differs from measured bundle: {name}")
        dependencies = json.loads((self.directory / "dependencies.json").read_text())["packages"]
        for package in ["numpy", "pandas", "scikit-learn", "xgboost", "catboost", "joblib"]:
            if importlib.metadata.version(package) != dependencies[package]:
                raise ValueError(f"Dependency version mismatch: {package}")
        self.preprocessor = joblib.load(self.directory / "preprocessor.joblib")
        self.models = {}
        for task, metadata in self.registry["models"].items():
            expected = HISTORY_FEATURES if metadata["contract"] == "history" else SINGLE_FEATURES
            if metadata["features"] != expected:
                raise ValueError(f"Feature schema mismatch: {task}")
            self.models[task] = joblib.load(self.directory / metadata["artifact"])

    def predict(self, records, contract="single", domain=DOMAIN):
        if domain != DOMAIN:
            raise ValueError("Incompatible protocol; use the matching cohort model")
        frame = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
        data = validate_raw(frame, history=contract == "history")
        if contract == "history" and (len(data) < 2 or data.battery_id.nunique() != 1):
            raise ValueError("History needs at least two observations from one battery")
        features = self.preprocessor.transform(frame, contract)
        predictions = np.asarray(self.models[f"{contract}_soh"].predict(features)).reshape(-1)
        notes = self.preprocessor.reliability(frame)
        indices = [int(np.argmax(data.cycle.to_numpy()))] if contract == "history" else range(len(data))
        results = []
        for i in indices:
            warnings = notes[i] + [self.registry["unsupported"],
                "RUL unavailable: primary-life 80% crossing does not define remaining second-life service; no justified second-life endpoint."]
            if contract == "history":
                if len(data) < 6:
                    warnings.append("Short observed history; missing past statistics are not invented.")
                if data.cycle.min() > 0:
                    warnings.append("Partial history; only supplied measurements are used.")
            if not self.registry["soh_training_range"][0] <= predictions[i] <= self.registry["soh_training_range"][1]:
                warnings.append("SOH prediction outside measured training target support.")
            results.append({"row_index": i,
                "metadata": {k: frame[k].iloc[i].item() if isinstance(frame[k].iloc[i], np.generic) else frame[k].iloc[i]
                             for k in ["battery_id", "row_id"] if k in frame and pd.notna(frame[k].iloc[i])},
                "soh": {"raw": float(predictions[i]), "display": float(np.clip(predictions[i], 0, 100)), "units": "%"},
                "rul": None, "reliability": {"status": "review_required", "warnings": warnings}})
        return {"pipeline_version": VERSION, "registry_sha256": self.registry_hash, "domain": DOMAIN,
                "contract": contract, "soh_definition": self.registry["soh_definition"],
                "rul_endpoint": self.registry["rul_endpoint"], "results": results}
