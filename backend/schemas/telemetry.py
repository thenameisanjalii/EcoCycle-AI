"""
EcoCycle AI — Pydantic Schemas for Battery Telemetry API
Task 2N — Production Inference API & Application Integration
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict


class BatteryCycleTelemetry(BaseModel):
    """
    Input schema for a single battery cycle telemetry record.
    Requires the exact 32 causal features established in Task 2M.4.
    Optional metadata (battery_id, row_id) is preserved without entering feature matrix X.
    """
    model_config = ConfigDict(extra="allow")

    # Raw Physical Measurements (6)
    IR: float = Field(..., description="Internal resistance in Ohms")
    QCharge: float = Field(..., description="Charge capacity in Ah")
    Tavg: float = Field(..., description="Average battery temperature during cycle in °C")
    Tmax: float = Field(..., description="Maximum battery temperature during cycle in °C")
    Tmin: float = Field(..., description="Minimum battery temperature during cycle in °C")
    chargetime: float = Field(..., description="Duration of charging process in minutes")

    # Temporal Dynamics (1)
    cycle: float = Field(..., description="Operating cycle number (>= 1)")

    # Anomaly & Sensor Fault Flags (2)
    IR_is_zero: float = Field(..., description="Binary flag indicating zero/null internal resistance (0 or 1)")
    temp_sensor_fault: float = Field(..., description="Binary flag indicating temperature sensor fault (0 or 1)")

    # First-Order Lags (4)
    IR_lag1: float = Field(..., description="Internal resistance from previous cycle (t-1)")
    IR_delta: float = Field(..., description="First derivative delta IR(t) - IR(t-1)")
    QCharge_lag1: float = Field(..., description="Charge capacity from previous cycle (t-1)")
    QCharge_delta: float = Field(..., description="First derivative delta QCharge(t) - QCharge(t-1)")
    Tavg_lag1: float = Field(..., description="Average temperature from previous cycle (t-1)")
    Tavg_delta: float = Field(..., description="First derivative delta Tavg(t) - Tavg(t-1)")
    chargetime_lag1: float = Field(..., description="Charge time from previous cycle (t-1)")
    chargetime_delta: float = Field(..., description="First derivative delta chargetime(t) - chargetime(t-1)")

    # Second-Order Acceleration (4)
    IR_accel: float = Field(..., description="Second derivative acceleration of internal resistance")
    QCharge_accel: float = Field(..., description="Second derivative acceleration of charge capacity")
    Tavg_accel: float = Field(..., description="Second derivative acceleration of temperature")
    chargetime_accel: float = Field(..., description="Second derivative acceleration of charge time")

    # Physical Ratios & Historical Trajectory (7)
    thermal_dissipation_rate: float = Field(..., description="Thermal gradient rate (Tmax - Tmin) / chargetime")
    charge_efficiency_proxy: float = Field(..., description="Charge throughput efficiency proxy QCharge / chargetime")
    resistance_growth_ratio: float = Field(..., description="Impedance growth ratio IR(t) / max(IR(t-1), 1e-6)")
    IR_roll_mean_5: float = Field(..., description="Historical 5-cycle backward rolling mean of internal resistance")
    IR_roll_std_5: float = Field(..., description="Historical 5-cycle backward rolling std of internal resistance")
    QCharge_roll_mean_5: float = Field(..., description="Historical 5-cycle backward rolling mean of charge capacity")
    QCharge_roll_std_5: float = Field(..., description="Historical 5-cycle backward rolling std of charge capacity")
    Tavg_roll_mean_5: float = Field(..., description="Historical 5-cycle backward rolling mean of temperature")
    Tavg_roll_std_5: float = Field(..., description="Historical 5-cycle backward rolling std of temperature")

    # Cumulative Degradation Slopes (2)
    cum_capacity_fade_rate: float = Field(..., description="Cumulative capacity fade rate relative to cycle 1")
    cum_resistance_growth_rate: float = Field(..., description="Cumulative resistance growth rate relative to cycle 1")

    # Optional Non-Predictive Metadata
    battery_id: Optional[Union[int, str]] = Field(None, description="Battery cell identifier (metadata only)")
    row_id: Optional[Union[int, str]] = Field(None, description="Client row identifier (metadata only)")


class BatchTelemetryRequest(BaseModel):
    """Batch prediction request schema."""
    records: List[BatteryCycleTelemetry] = Field(..., description="List of battery cycle records (max 5,000)")


class ValueOutputDetail(BaseModel):
    """Dual-output prediction details separating raw authoritative outputs from display values."""
    raw: float = Field(..., description="Authoritative unclipped regression prediction")
    display: float = Field(..., description="Presentation-safe display value bounded for UI sanity")
    units: str = Field(..., description="Physical units of the target measurement")


class TargetInterpretation(BaseModel):
    """Deterministic, rule-based operational interpretation."""
    category: str = Field(..., description="Operational regime category")
    description: str = Field(..., description="Explanatory guidance based on Task 2L.3 regimes")
    confidence_note: str = Field(..., description="Operational confidence or regime-specific uncertainty note")


class PredictionResponse(BaseModel):
    """Response schema for single record prediction."""
    status: str = Field("success", description="Execution status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Preserved client metadata (e.g., battery_id, row_id)")
    predictions: Dict[str, ValueOutputDetail] = Field(..., description="Dual-output predictions for SOH and RUL")
    interpretation: Dict[str, TargetInterpretation] = Field(..., description="Rule-based degradation regime interpretations")
    models: Dict[str, Any] = Field(..., description="Model provenance and architecture metadata")


class BatchPredictionRecord(BaseModel):
    """Single item in batch prediction response."""
    row_index: int = Field(..., description="Zero-based index of the input record")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Preserved client metadata")
    predictions: Dict[str, ValueOutputDetail] = Field(..., description="Dual-output predictions for SOH and RUL")
    interpretation: Dict[str, TargetInterpretation] = Field(..., description="Rule-based degradation regime interpretations")


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions."""
    status: str = Field("success", description="Execution status")
    total_records: int = Field(..., description="Number of scored records")
    results: List[BatchPredictionRecord] = Field(..., description="Scored records preserving row association")
    models: Dict[str, Any] = Field(..., description="Model provenance and architecture metadata")


class ModelInfoResponse(BaseModel):
    """Response schema for model provenance and registry information."""
    project: str = Field(..., description="Project name")
    pipeline_stage: str = Field(..., description="Certified pipeline stage")
    dataset_sha256: str = Field(..., description="Verified SHA-256 digest of raw master_dataset.csv")
    models: Dict[str, Any] = Field(..., description="Model details, hyperparams, and validation/test metrics")
