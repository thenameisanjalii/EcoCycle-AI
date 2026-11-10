"""
EcoCycle AI — Production-Safe Model Inference Pipeline
Task 2M.4 — Final Model Packaging & Inference Pipeline

Provides standardized inference interfaces for:
1. predict_soh(input_data): Predict State of Health (%)
2. predict_rul(input_data): Predict Remaining Useful Life (cycles, raw & unclipped)
3. predict_all(input_data): Combined prediction output with model metadata
4. predict_batch(df_or_csv, output_path): Batch CSV / DataFrame scoring preserving inputs
5. format_presentation_output(raw_soh, raw_rul): Explicit presentation layer (non-destructive)
"""

import os
import argparse
from pathlib import Path
from typing import Union, Dict, Any, Optional, List
import numpy as np
import pandas as pd

from .final_registry import get_default_registry, FinalModelRegistry
from .input_validation import validate_inference_input, InputValidationError, DataLeakageError
from .feature_schema import ADVANCED_FEATURE_COLUMNS

PIPELINE_VERSION = "1.0.0"


def predict_soh(
    input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.Series, pd.DataFrame],
    registry: Optional[FinalModelRegistry] = None
) -> Union[float, np.ndarray]:
    """
    Predicts State of Health (SOH) in percentage capacity retention.

    Args:
        input_data: Single dictionary, list of dicts, pd.Series, or pd.DataFrame containing
                    the approved 32 causal features.
        registry: Optional FinalModelRegistry instance.

    Returns:
        float if single record, or np.ndarray of float64 for batch.
    """
    reg = registry or get_default_registry()
    X, _ = validate_inference_input(input_data, target="soh")
    model = reg.load_model("soh")
    preds = model.predict(X)

    if len(preds) == 1:
        return float(preds[0])
    return preds.astype(np.float64)


def predict_rul(
    input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.Series, pd.DataFrame],
    registry: Optional[FinalModelRegistry] = None
) -> Union[float, np.ndarray]:
    """
    Predicts Remaining Useful Life (RUL) in operating cycles.

    NOTE: Raw model predictions are strictly preserved. Predictions are NOT
    silently clipped or rounded. If presentation bounds are required, use
    format_presentation_output().

    Args:
        input_data: Single dictionary, list of dicts, pd.Series, or pd.DataFrame containing
                    the approved 32 causal features.
        registry: Optional FinalModelRegistry instance.

    Returns:
        float if single record, or np.ndarray of float64 for batch.
    """
    reg = registry or get_default_registry()
    X, _ = validate_inference_input(input_data, target="rul")
    model = reg.load_model("rul")
    preds = model.predict(X)

    if len(preds) == 1:
        return float(preds[0])
    return preds.astype(np.float64)


def predict_all(
    input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.Series, pd.DataFrame],
    registry: Optional[FinalModelRegistry] = None,
    enforce_physical_bounds: bool = True
) -> Dict[str, Any]:
    """
    Predicts both SOH and RUL for the provided input data, returning a structured
    dictionary including model versioning and raw numerical predictions.

    Args:
        input_data: Single record or batch containing the approved 32 causal features.
        registry: Optional FinalModelRegistry instance.

    Returns:
        dict:
            - predicted_soh: float or list of floats
            - predicted_rul: float or list of floats (raw, unclipped)
            - model_versions: metadata dictionary
    """
    reg = registry or get_default_registry()
    X, _ = validate_inference_input(
        input_data,
        target=None,
        enforce_physical_bounds=enforce_physical_bounds
    )

    soh_model = reg.load_model("soh")
    rul_model = reg.load_model("rul")

    soh_preds = soh_model.predict(X)
    rul_preds = rul_model.predict(X)

    soh_meta = reg.get_model_metadata("soh")
    rul_meta = reg.get_model_metadata("rul")

    if len(X) == 1:
        out_soh = float(soh_preds[0])
        out_rul = float(rul_preds[0])
    else:
        out_soh = [float(x) for x in soh_preds]
        out_rul = [float(x) for x in rul_preds]

    return {
        "predicted_soh": out_soh,
        "predicted_rul": out_rul,
        "model_versions": {
            "pipeline_version": PIPELINE_VERSION,
            "soh_model_id": soh_meta["model_id"],
            "soh_framework": f"{soh_meta['framework']} {soh_meta['framework_version']}",
            "rul_model_id": rul_meta["model_id"],
            "rul_framework": f"{rul_meta['framework']} {rul_meta['framework_version']}",
            "feature_set": "32_causal_features"
        }
    }


def predict_batch(
    data_or_path: Union[str, pd.DataFrame],
    output_path: Optional[str] = None,
    registry: Optional[FinalModelRegistry] = None
) -> pd.DataFrame:
    """
    Performs non-destructive batch inference on a DataFrame or CSV file.
    All original input columns, ordering, and row identifiers are preserved.

    Appends:
        - 'predicted_soh': raw SOH regression prediction (%)
        - 'predicted_rul': raw RUL regression prediction (cycles, unclipped)

    Args:
        data_or_path: Path to CSV file or existing DataFrame.
        output_path: Optional path to save resulting enriched CSV.
        registry: Optional FinalModelRegistry instance.

    Returns:
        pd.DataFrame: Copy of input with prediction columns appended.
    """
    if isinstance(data_or_path, str):
        if not Path(data_or_path).exists():
            raise FileNotFoundError(f"Input file not found: {data_or_path}")
        df = pd.read_csv(data_or_path)
    elif isinstance(data_or_path, pd.DataFrame):
        df = data_or_path.copy()
    else:
        raise InputValidationError(f"Expected CSV path or DataFrame, got {type(data_or_path)}")

    results = predict_all(df, registry=registry)

    df_out = df.copy()
    df_out["predicted_soh"] = results["predicted_soh"]
    df_out["predicted_rul"] = results["predicted_rul"]

    if output_path:
        Path(output_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(output_path, index=False)

    return df_out


def format_presentation_output(
    raw_soh: Union[float, np.ndarray, list],
    raw_rul: Union[float, np.ndarray, list]
) -> Dict[str, Any]:
    """
    Presentation Layer Helper: Applies operational bounds for UI display.
    CRITICAL: This layer DOES NOT overwrite or replace raw predictions.
    Both raw and presentation values are returned side-by-side.

    Rules:
        - display_soh: clipped between [0.0%, 100.0%] for user UI sanity.
        - display_rul: bounded at >= 0.0 cycles (e.g. negative terminal predictions -> 0).
    """
    def _bound_soh(val: float) -> float:
        return float(np.clip(val, 0.0, 100.0))

    def _bound_rul(val: float) -> float:
        return float(max(val, 0.0))

    if isinstance(raw_soh, (int, float)) and isinstance(raw_rul, (int, float)):
        return {
            "raw_soh": float(raw_soh),
            "raw_rul": float(raw_rul),
            "display_soh": _bound_soh(raw_soh),
            "display_rul": _bound_rul(raw_rul),
            "presentation_note": "Display values bounded at [0%, 100%] for SOH and >= 0 for RUL. Raw predictions remain authoritative."
        }
    else:
        soh_arr = np.array(raw_soh, dtype=np.float64)
        rul_arr = np.array(raw_rul, dtype=np.float64)
        return {
            "raw_soh": soh_arr.tolist(),
            "raw_rul": rul_arr.tolist(),
            "display_soh": np.clip(soh_arr, 0.0, 100.0).tolist(),
            "display_rul": np.maximum(rul_arr, 0.0).tolist(),
            "presentation_note": "Display values bounded at [0%, 100%] for SOH and >= 0 for RUL. Raw predictions remain authoritative."
        }


def main():
    parser = argparse.ArgumentParser(description="EcoCycle AI — Model Inference Engine")
    parser.add_argument("--input", required=True, help="Path to input CSV containing 32 causal features")
    parser.add_argument("--output", required=False, default=None, help="Path to save enriched predictions CSV")
    parser.add_argument("--target", choices=["soh", "rul", "both"], default="both", help="Prediction target")

    args = parser.parse_args()

    print(f"Loading input data from: {args.input}")
    df_in = pd.read_csv(args.input)

    if args.target == "soh":
        preds = predict_soh(df_in)
        df_in["predicted_soh"] = preds
    elif args.target == "rul":
        preds = predict_rul(df_in)
        df_in["predicted_rul"] = preds
    else:
        df_in = predict_batch(df_in)

    if args.output:
        df_in.to_csv(args.output, index=False)
        print(f"Predictions saved to: {args.output}")
    else:
        print(df_in.head())


if __name__ == "__main__":
    main()
