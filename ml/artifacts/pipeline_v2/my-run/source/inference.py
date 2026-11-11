"""Offline/API entry point. All v2 consumers use the same hashed bundle."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import VERSION
from .preprocessing import validate_raw, SINGLE_FEATURES, HISTORY_FEATURES


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ModelBundle:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        registry_path = self.directory / "registry.json"
        expected = (self.directory / "registry.sha256").read_text().strip()
        if digest(registry_path) != expected:
            raise ValueError("Registry hash mismatch.")
        self.registry_hash = expected
        self.registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if self.registry["version"] != VERSION:
            raise ValueError("Unsupported pipeline version.")
        for name, expected_hash in self.registry["files"].items():
            path = (self.directory / name).resolve()
            if not path.is_relative_to(self.directory) or digest(path) != expected_hash:
                raise ValueError(f"Artifact hash mismatch: {name}")
        for name in ["__init__.py", "preprocessing.py", "inference.py"]:
            if digest(Path(__file__).parent / name) != digest(self.directory / "source" / name):
                raise ValueError(f"Runtime source differs from versioned bundle: {name}")
        dependencies = json.loads((self.directory / "dependencies.json").read_text(encoding="utf-8"))["packages"]
        for package in ["numpy", "pandas", "scikit-learn", "xgboost", "catboost", "joblib"]:
            if importlib.metadata.version(package) != dependencies[package]:
                raise ValueError(f"Dependency version mismatch for {package}; use requirements-lock.txt.")
        self.preprocessor = joblib.load(self.directory / "preprocessor.joblib")
        self.models = {}
        for task, metadata in self.registry["models"].items():
            schema = HISTORY_FEATURES if metadata["contract"] == "history" else SINGLE_FEATURES
            if metadata["features"] != schema:
                raise ValueError(f"Feature schema mismatch: {task}")
            self.models[task] = joblib.load(self.directory / metadata["artifact"])

    def predict(self, records, contract="single"):
        frame = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
        d = validate_raw(frame, history=contract == "history")
        if contract == "history":
            if d.battery_id.nunique() != 1:
                raise ValueError("A history request must contain exactly one battery. Submit batteries separately.")
            if len(d) < 2:
                raise ValueError("History needs at least two observed cycles; use single assessment for one record.")
        x = self.preprocessor.transform(frame, contract)
        notes = self.preprocessor.reliability(frame)
        task = f"{contract}_soh"
        if task not in self.models:
            raise ValueError(f"SOH model unavailable for contract: {contract}")
        soh = np.asarray(self.models[task].predict(x)).reshape(-1)
        rul = None
        if contract == "history" and "history_rul" in self.models:
            rul = np.asarray(self.models["history_rul"].predict(x)).reshape(-1)
        indices = [int(np.argmax(d.cycle.to_numpy()))] if contract == "history" else range(len(d))
        results = []
        for i in indices:
            warnings = list(notes[i])
            warnings.append(self.registry["unsupported"])
            if contract == "single":
                warnings.append("RUL requires observed history and is unavailable for single assessment.")
            else:
                warnings.append("RUL is conditional on the confirmed-failure training cohort; censoring selection bias remains.")
                if len(d) < 6:
                    warnings.append("Short history: fewer than five preceding observations; historical statistics may be unavailable.")
                if d.cycle.min() > 2:
                    warnings.append("History begins after early life; features use only the supplied window, and full-history evaluation may not represent this window.")
                if rul is None:
                    warnings.append("RUL model unavailable: insufficient confirmed failures in one or more splits.")
            if not self.registry["soh_training_range"][0] <= float(soh[i]) <= self.registry["soh_training_range"][1]:
                warnings.append("SOH prediction outside measured training target support.")
            # A numerical estimate does not certify reliability or narrow uncertainty.
            unreliable = bool(notes[i]) or (contract == "history" and (len(d) < 6 or d.cycle.min() > 2))
            results.append({"row_index": i,
                            "metadata": {k: frame[k].iloc[i].item() if isinstance(frame[k].iloc[i], np.generic) else frame[k].iloc[i]
                                         for k in ["battery_id", "row_id"] if k in frame and pd.notna(frame[k].iloc[i])},
                            "soh": {"raw": float(soh[i]), "display": float(np.clip(soh[i], 0, 100)), "units": "%"},
                            "rul": None if rul is None else {"raw": float(rul[i]), "display": float(max(0, rul[i])), "units": "cycles"},
                            "reliability": {"status": "review_required" if unreliable else "within_feature_support_not_a_confidence_interval",
                                            "warnings": warnings}})
        return {"pipeline_version": VERSION, "registry_sha256": self.registry_hash, "contract": contract,
                "soh_definition": self.registry["soh_definition"], "rul_endpoint": self.registry["rul_endpoint"], "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--input", required=True, help="CSV with raw measured telemetry; no targets or engineered features")
    parser.add_argument("--contract", choices=["single", "history"], default="single")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = ModelBundle(args.bundle).predict(pd.read_csv(args.input), args.contract)
    with open(args.output, "x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
