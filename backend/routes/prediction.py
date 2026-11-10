"""
EcoCycle AI — API Route Endpoints
Task 2N — Production Inference API & Application Integration
"""

import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Request
import pandas as pd
import joblib

from ml.models.final_registry import get_default_registry, FinalModelRegistry, ModelRegistryError
from ml.models.input_validation import validate_inference_input, InputValidationError, DataLeakageError
from ml.models.config import PREPROCESSOR_PATHS
from ml.preprocessing.pipeline import prepare_inference_features
from ml.models.inference import (
    predict_all,
    predict_batch,
    format_presentation_output,
    PIPELINE_VERSION
)
from backend.schemas.telemetry import (
    BatteryCycleTelemetry,
    HistoricalBatteryRequest,
    BatchTelemetryRequest,
    PredictionResponse,
    BatchPredictionResponse,
    ModelInfoResponse,
    ValueOutputDetail,
    TargetInterpretation,
    BatchPredictionRecord
)
from backend.services.interpretation import interpret_battery_health

router = APIRouter()

MAX_BATCH_SIZE = 5000


@router.get("/health", status_code=status.HTTP_200_OK)
def get_health() -> Dict[str, Any]:
    """Health check endpoint verifying API service and model availability."""
    reg = get_default_registry()
    soh_model = reg.load_model("soh")
    rul_model = reg.load_model("rul")

    return {
        "status": "healthy",
        "service": "EcoCycle AI Battery Health API",
        "pipeline_version": PIPELINE_VERSION,
        "models_available": {
            "soh": soh_model is not None,
            "rul": rul_model is not None
        }
    }


@router.get("/model-info", response_model=ModelInfoResponse, status_code=status.HTTP_200_OK)
def get_model_info() -> Dict[str, Any]:
    """Returns complete model registry provenance, architectures, and certified metrics."""
    reg = get_default_registry()
    data = reg.registry_data
    return {
        "project": data.get("project", "EcoCycle AI"),
        "pipeline_stage": data.get("pipeline_stage", "Task 2M.4"),
        "dataset_sha256": data.get("dataset_sha256", ""),
        "models": data.get("models", {})
    }


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_single_cycle(history: HistoricalBatteryRequest) -> Dict[str, Any]:
    """
    Accepts raw historical battery-cycle records and derives the 32 causal features.
    Returns authoritative raw predictions, presentation display values, regime interpretation, and provenance.
    """
    if not history.records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Historical battery record list is empty."
        )
    if len(history.records) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"History size {len(history.records)} exceeds maximum permissible limit of {MAX_BATCH_SIZE} records."
        )
    if any(record.cycle < 1.0 for record in history.records):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input validation error: physical bound violation for feature 'cycle'."
        )

    try:
        history_df = pd.DataFrame([record.model_dump() for record in history.records])
        preprocessor = joblib.load(PREPROCESSOR_PATHS["soh"])
        features_df = prepare_inference_features(history_df, preprocessor).tail(1)
        X, metadata_df = validate_inference_input(
            features_df,
            enforce_physical_bounds=False
        )
    except DataLeakageError as dle:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data leakage rejected: {dle}"
        )
    except InputValidationError as ive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation error: {ive}"
        )
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to prepare historical records for inference: {exc}"
        )

    # 1. Inference via Certified Engine
    res = predict_all(X, enforce_physical_bounds=False)
    raw_soh = float(res["predicted_soh"])
    raw_rul = float(res["predicted_rul"])

    # 2. Presentation Bounding (Non-Destructive)
    pres = format_presentation_output(raw_soh, raw_rul)

    # 3. Degradation Interpretation
    interp = interpret_battery_health(raw_soh, raw_rul)

    # 4. Build Structured Response
    latest_record = history_df.sort_values("cycle").iloc[-1].to_dict()
    client_meta = {
        k: v for k, v in latest_record.items()
        if k in ["battery_id", "row_id"] and v is not None
    }

    return {
        "status": "success",
        "metadata": client_meta,
        "predictions": {
            "soh": {
                "raw": pres["raw_soh"],
                "display": pres["display_soh"],
                "units": "%"
            },
            "rul": {
                "raw": pres["raw_rul"],
                "display": pres["display_rul"],
                "units": "cycles"
            }
        },
        "interpretation": interp,
        "models": res["model_versions"]
    }


@router.post("/predict/batch", response_model=BatchPredictionResponse, status_code=status.HTTP_200_OK)
def predict_batch_cycles(batch: BatchTelemetryRequest) -> Dict[str, Any]:
    """
    Accepts a batch of battery-cycle telemetry records (max 5,000).
    Returns predictions while preserving client metadata and input row association.
    """
    if len(batch.records) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch list of telemetry records is empty."
        )

    if len(batch.records) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size {len(batch.records)} exceeds maximum permissible limit of {MAX_BATCH_SIZE} records."
        )

    raw_records = [r.model_dump() for r in batch.records]

    # Convert to DataFrame and Validate
    df_raw = pd.DataFrame(raw_records)
    try:
        X, meta_df = validate_inference_input(df_raw)
    except DataLeakageError as dle:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data leakage rejected: {dle}"
        )
    except InputValidationError as ive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation error: {ive}"
        )

    # Run Certified Inference
    res = predict_all(X)
    soh_list = res["predicted_soh"]
    rul_list = res["predicted_rul"]

    # Format Output List
    results = []
    for idx in range(len(raw_records)):
        rec = raw_records[idx]
        raw_s = float(soh_list[idx])
        raw_r = float(rul_list[idx])
        pres = format_presentation_output(raw_s, raw_r)
        interp = interpret_battery_health(raw_s, raw_r)

        client_meta = {k: rec[k] for k in ["battery_id", "row_id"] if k in rec and rec[k] is not None}

        results.append({
            "row_index": idx,
            "metadata": client_meta,
            "predictions": {
                "soh": {
                    "raw": pres["raw_soh"],
                    "display": pres["display_soh"],
                    "units": "%"
                },
                "rul": {
                    "raw": pres["raw_rul"],
                    "display": pres["display_rul"],
                    "units": "cycles"
                }
            },
            "interpretation": interp
        })

    return {
        "status": "success",
        "total_records": len(results),
        "results": results,
        "models": res["model_versions"]
    }
