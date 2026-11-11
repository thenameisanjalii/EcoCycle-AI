"""Strict request schemas for battery prediction endpoints."""

from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RawTelemetryRecord(BaseModel):
    """Validated telemetry and causal-history values accepted by prediction."""

    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

    @model_validator(mode='before')
    @classmethod
    def reject_leakage_fields(cls, value):
        if isinstance(value, dict):
            leakage_fields = {
                "QDischarge",
                "SOH",
                "RUL",
                "max_cycle",
            } & value.keys()
            if leakage_fields:
                fields = ", ".join(sorted(leakage_fields))
                raise ValueError(f"Data leakage rejected: forbidden field(s): {fields}")
        return value

    IR: float = Field(..., description="Internal resistance in Ohms")
    QCharge: float = Field(..., description="Charge capacity in Ah")
    Tavg: float = Field(..., description="Average battery temperature during cycle in °C")
    Tmax: float = Field(..., description="Maximum battery temperature during cycle in °C")
    Tmin: float = Field(..., description="Minimum battery temperature during cycle in °C")
    chargetime: float = Field(..., description="Duration of charging process in minutes")
    cycle: float = Field(..., description="Operating cycle number")
    IR_is_zero: float = Field(..., description="Zero internal-resistance indicator")
    temp_sensor_fault: float = Field(..., description="Temperature sensor fault indicator")
    IR_lag1: float = Field(..., description="Previous-cycle internal resistance")
    IR_delta: float = Field(..., description="Internal-resistance first difference")
    QCharge_lag1: float = Field(..., description="Previous-cycle charge capacity")
    QCharge_delta: float = Field(..., description="Charge-capacity first difference")
    Tavg_lag1: float = Field(..., description="Previous-cycle average temperature")
    Tavg_delta: float = Field(..., description="Average-temperature first difference")
    chargetime_lag1: float = Field(..., description="Previous-cycle charge time")
    chargetime_delta: float = Field(..., description="Charge-time first difference")
    battery_id: Union[int, str] = Field(..., description="Battery cell identifier")
    row_id: Optional[Union[int, str]] = Field(None, description="Client row identifier")


class HistoricalBatteryRequest(BaseModel):
    """Raw historical battery records used to derive causal inference features."""

    records: list[RawTelemetryRecord] = Field(
        ...,
        description="Chronological raw battery records used to generate model features",
    )
