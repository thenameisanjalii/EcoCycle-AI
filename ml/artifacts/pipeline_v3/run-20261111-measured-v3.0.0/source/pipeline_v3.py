"""Explicit opt-in for the separate 50C C/3 characterization research cohort."""
import os
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ml.pipeline_v3.inference import ModelBundle

router = APIRouter(prefix="/v3", tags=["Measured characterization research cohort"])


class Measurement(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    QCharge: float = Field(..., gt=0, le=2, description="Measured C/3 charge capacity, Ah")
    chargetime: float = Field(..., gt=0, le=10000, description="Measured C/3 charge step duration, minutes")
    cycle: int = Field(..., ge=0, le=100000)
    battery_id: str | int | None = None
    row_id: str | int | None = None


class MeasurementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain: Literal["wheeler_C3_50C"]
    contract: Literal["single", "history"] = "single"
    records: list[Measurement] = Field(..., min_length=1, max_length=5000)


@lru_cache(maxsize=1)
def get_bundle():
    directory = os.environ.get("ECOCYCLE_V3_BUNDLE")
    if not directory:
        raise HTTPException(503, "Set ECOCYCLE_V3_BUNDLE to a completed measured research run")
    try:
        return ModelBundle(directory)
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(503, f"Measured bundle unavailable: {exc}") from exc


@router.get("/model-info")
def model_info():
    bundle = get_bundle()
    return {"registry_sha256": bundle.registry_hash, "registry": bundle.registry}


@router.post("/predict")
def predict(request: MeasurementRequest):
    try:
        return get_bundle().predict([r.model_dump(exclude_none=True) for r in request.records], request.contract, request.domain)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
