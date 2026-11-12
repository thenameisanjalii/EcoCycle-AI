"""Explicit measurement-only and observed-history API contracts."""
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ml.pipeline_v2.inference import ModelBundle

router = APIRouter(prefix="/v2", tags=["Versioned measurement pipeline"])
DEFAULT_BUNDLE = Path(__file__).resolve().parents[2] / "ml/artifacts/pipeline_v2/run-20261111-v2.0.1"


class Measurement(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    IR: float | None = None
    QCharge: float = Field(..., gt=0, le=20, description="Measured charge capacity in Ah; never substituted for QDischarge")
    Tavg: float | None = None
    Tmax: float | None = None
    Tmin: float | None = None
    chargetime: float | None = Field(None, ge=0, le=100000, description="Minutes, not seconds")
    cycle: float = Field(..., ge=1, le=100000)
    battery_id: str | int | None = None
    row_id: str | int | None = None


class MeasurementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract: Literal["single", "history"] = "single"
    records: list[Measurement] = Field(..., min_length=1, max_length=5000)


@lru_cache(maxsize=1)
def get_bundle():
    directory = os.environ.get("ECOCYCLE_V2_BUNDLE") or str(DEFAULT_BUNDLE)
    try:
        return ModelBundle(directory)
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(503, f"Versioned bundle unavailable: {exc}") from exc


@router.get("/model-info")
def model_info():
    bundle = get_bundle()
    return {"registry_sha256": bundle.registry_hash, "registry": bundle.registry}


@router.get("/health")
def health():
    bundle = get_bundle()
    return {"status": "healthy", "service": "EcoCycle AI v2", "pipeline_version": bundle.registry["version"],
            "models_available": {"soh": "single_soh" in bundle.models, "rul": "history_rul" in bundle.models}}


@router.post("/predict")
def predict(request: MeasurementRequest):
    try:
        return get_bundle().predict([r.model_dump(exclude_none=True) for r in request.records], request.contract)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
