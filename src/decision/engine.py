"""
EcoCycle AI — Second-Life Decision Engine
Task 2O — Second-Life Decision Engine

Core engine that coordinates legitimate ML inference and deterministic decision logic.
"""

from typing import Dict, Any, Optional, Union, List
import numpy as np
import pandas as pd

from src.models.final_registry import get_default_registry, FinalModelRegistry
from src.models.inference import predict_all, format_presentation_output, PIPELINE_VERSION
from src.models.input_validation import validate_inference_input
from .rules import evaluate_second_life_decision
from .constants import DECISION_DISCLAIMER


class SecondLifeDecisionEngine:
    """
    Coordinates certified model inference and deterministic decision matrix evaluation.
    Leaves model estimators and artifacts completely immutable.
    """
    ENGINE_VERSION = "task_2o_v1"

    def __init__(self, registry: Optional[FinalModelRegistry] = None):
        self.registry = registry or get_default_registry()
        soh_meta = self.registry.get_model_metadata("soh")
        rul_meta = self.registry.get_model_metadata("rul")
        dataset_sha = self.registry.registry_data.get("dataset_sha256", "")
        self.provenance = {
            "pipeline_version": PIPELINE_VERSION,
            "soh_model_id": soh_meta["model_id"],
            "soh_framework": f"{soh_meta['framework']} {soh_meta['framework_version']}",
            "rul_model_id": rul_meta["model_id"],
            "rul_framework": f"{rul_meta['framework']} {rul_meta['framework_version']}",
            "feature_set": "32_causal_features",
            "dataset_sha256": dataset_sha,
            "decision_engine": "task_2o_v1",
            "decision_type": "project-defined deterministic business rules"
        }

    def assess_from_predictions(
        self,
        raw_soh: float,
        raw_rul: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates decision from already-inferred raw predictions.
        Preserves raw values unclipped while calculating display bounds.
        """
        pres = format_presentation_output(raw_soh, raw_rul)
        disp_soh = pres["display_soh"]
        disp_rul = pres["display_rul"]

        decision_eval = evaluate_second_life_decision(
            raw_soh=raw_soh,
            raw_rul=raw_rul,
            display_soh=disp_soh,
            display_rul=disp_rul
        )

        return {
            "status": "success",
            "metadata": metadata or {},
            "decision": decision_eval["decision"],
            "predictions": {
                "soh": {
                    "raw": float(raw_soh),
                    "display": float(disp_soh),
                    "units": "%"
                },
                "rul": {
                    "raw": float(raw_rul),
                    "display": float(disp_rul),
                    "units": "cycles"
                }
            },
            "regimes": decision_eval["regimes"],
            "reasoning": decision_eval["reasoning"],
            "rules": decision_eval["rules"],
            "provenance": self.provenance,
            "disclaimer": DECISION_DISCLAIMER
        }

    def assess_telemetry(
        self,
        telemetry_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        End-to-end evaluation pipeline:
        1. Validates telemetry input and enforces anti-leakage rules.
        2. Performs certified SOH & RUL ML inference.
        3. Applies deterministic second-life decision rules.
        4. Preserves client metadata and returns unified response.
        """
        # Validate through existing certified input validation
        X, meta_df = validate_inference_input(telemetry_record)

        # Execute certified inference
        preds = predict_all(X, registry=self.registry)
        raw_soh = float(preds["predicted_soh"])
        raw_rul = float(preds["predicted_rul"])

        # Extract client metadata
        client_meta = {
            k: v for k, v in telemetry_record.items()
            if k in ["battery_id", "row_id"] and v is not None
        }

        return self.assess_from_predictions(raw_soh, raw_rul, metadata=client_meta)


_default_engine: Optional[SecondLifeDecisionEngine] = None

def get_default_decision_engine() -> SecondLifeDecisionEngine:
    """Returns the singleton instance of SecondLifeDecisionEngine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = SecondLifeDecisionEngine()
    return _default_engine
