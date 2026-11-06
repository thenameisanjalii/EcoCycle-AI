"""
EcoCycle AI — Pydantic Schemas for Second-Life Decision Engine
Task 2O — Second-Life Decision Engine
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from .constants import DECISION_DISCLAIMER


class DecisionDetail(BaseModel):
    """Specific decision output including category, suggested second-life application, and rule strength."""
    category: str = Field(..., description="Lifecycle decision: PRIMARY_OPERATION, SECOND_LIFE_CANDIDATE, or MATERIAL_RECYCLING")
    recommended_application: str = Field(..., description="Recommended repurposing application or operational directive")
    decision_strength: str = Field(..., description="Qualitative decision rule clarity: STRONG, MODERATE, or REVIEW_REQUIRED")


class ValuePredictionDetail(BaseModel):
    """Dual-output prediction details separating raw authoritative regression numbers from bounded display values."""
    raw: float = Field(..., description="Authoritative unclipped regression output from certified ML estimator")
    display: float = Field(..., description="Presentation-safe display value bounded for user-facing sanity")
    units: str = Field(..., description="Physical units of measurement (% for SOH, cycles for RUL)")


class PredictionsSummary(BaseModel):
    """Dual-target predictions for State of Health (SOH) and Remaining Useful Life (RUL)."""
    soh: ValuePredictionDetail = Field(..., description="SOH prediction values")
    rul: ValuePredictionDetail = Field(..., description="RUL prediction values")


class RegimeDetail(BaseModel):
    """Lifecycle degradation regime classifications."""
    soh: str = Field(..., description="SOH degradation regime (e.g. HEALTHY_NORMAL_AGING)")
    rul: str = Field(..., description="RUL operational regime (e.g. MID_LIFE)")


class RuleThresholdsDetail(BaseModel):
    """Transparent definitions of project-defined evaluation thresholds."""
    soh_thresholds: Dict[str, str] = Field(..., description="Empirical SOH threshold definitions")
    rul_thresholds: Dict[str, str] = Field(..., description="Empirical RUL threshold definitions")


class ProvenanceDetail(BaseModel):
    """Model and decision engine provenance metadata."""
    pipeline_version: str = Field(..., description="Pipeline version (1.0.0)")
    soh_model_id: str = Field(..., description="Certified SOH model ID")
    soh_framework: Optional[str] = Field(None, description="SOH framework and version")
    rul_model_id: str = Field(..., description="Certified RUL model ID")
    rul_framework: Optional[str] = Field(None, description="RUL framework and version")
    feature_set: Optional[str] = Field(None, description="Feature set schema name")
    dataset_sha256: Optional[str] = Field(None, description="SHA-256 digest of training dataset")
    decision_engine: str = Field("task_2o_v1", description="Decision engine version identifier")
    decision_type: str = Field(
        "project-defined deterministic business rules",
        description="Type of decision logic applied"
    )


class SecondLifeAssessmentResponse(BaseModel):
    """Complete unified API response schema for second-life battery assessment."""
    status: str = Field("success", description="Execution status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Preserved client metadata (e.g., battery_id, row_id)")
    decision: DecisionDetail = Field(..., description="Second-life assessment recommendation")
    predictions: PredictionsSummary = Field(..., description="Dual-target SOH and RUL model predictions")
    regimes: RegimeDetail = Field(..., description="Degradation regimes corresponding to predicted outputs")
    reasoning: List[str] = Field(..., description="Step-by-step deterministic rationale explaining the decision")
    rules: RuleThresholdsDetail = Field(..., description="Threshold reference dictionary")
    provenance: ProvenanceDetail = Field(..., description="Model and engine provenance")
    disclaimer: str = Field(DECISION_DISCLAIMER, description="Methodological limitation and safety disclaimer")
