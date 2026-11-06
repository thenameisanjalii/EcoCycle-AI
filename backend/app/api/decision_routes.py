"""
EcoCycle AI — Second-Life Decision Engine API Routes
Task 2O — Second-Life Decision Engine

Exposes the POST /decision/assess endpoint for end-to-end battery lifecycle assessment.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.telemetry import BatteryCycleTelemetry
from src.models.input_validation import validate_inference_input, InputValidationError, DataLeakageError
from src.models.inference import predict_all
from src.decision.engine import get_default_decision_engine
from src.decision.schemas import SecondLifeAssessmentResponse

decision_router = APIRouter(tags=["Second-Life Decision Engine"])


@decision_router.post(
    "/decision/assess",
    response_model=SecondLifeAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess Battery Second-Life Viability & Lifecycle Recommendation"
)
def assess_battery_second_life(telemetry: BatteryCycleTelemetry) -> Dict[str, Any]:
    """
    Evaluates battery State of Health (SOH) and Remaining Useful Life (RUL)
    using certified ML estimators, then executes the deterministic Task 2O decision matrix
    to produce an actionable second-life lifecycle recommendation.

    - Input: 32 causal degradation features + optional non-predictive metadata (battery_id, row_id).
    - Guarantees: Zero future leakage, raw prediction preservation, deterministic rule evaluation.
    """
    record_dict = telemetry.model_dump()

    # 1. Validation & Leakage Check
    try:
        X, meta_df = validate_inference_input(record_dict)
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

    # 2. Certified ML Inference
    res = predict_all(X)
    raw_soh = float(res["predicted_soh"])
    raw_rul = float(res["predicted_rul"])

    # 3. Extract preserved client metadata
    client_meta = {
        k: v for k, v in record_dict.items()
        if k in ["battery_id", "row_id"] and v is not None
    }

    # 4. Execute Task 2O Deterministic Decision Engine
    engine = get_default_decision_engine()
    assessment = engine.assess_from_predictions(raw_soh, raw_rul, metadata=client_meta)

    return assessment
