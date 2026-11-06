"""
EcoCycle AI — Final Feature Schema & Causal Specification Module
Task 2M.4 — Final Model Packaging & Inference Pipeline

Provides canonical definitions of:
1. Baseline 17-feature schema (Feature Set A)
2. Candidate 15-feature causal extensions
3. Full 32-feature advanced schema (Feature Set B)
4. Functional feature groups
5. Forbidden leakage columns & anti-leakage guards
6. Physical admissibility boundaries for input sensor validation
"""

from typing import List, Dict, Any, Tuple

# 1. Baseline 17 features established in Task 2K and locked in Task 2L
BASELINE_FEATURE_COLUMNS: List[str] = [
    "IR",
    "QCharge",
    "Tavg",
    "Tmax",
    "Tmin",
    "chargetime",
    "cycle",
    "IR_is_zero",
    "temp_sensor_fault",
    "IR_lag1",
    "IR_delta",
    "QCharge_lag1",
    "QCharge_delta",
    "Tavg_lag1",
    "Tavg_delta",
    "chargetime_lag1",
    "chargetime_delta"
]

# 2. 15 Advanced Candidate Causal Features added in Task 2M
CANDIDATE_CAUSAL_FEATURES: List[str] = [
    # Second-order rate of change (acceleration)
    "IR_accel",
    "QCharge_accel",
    "Tavg_accel",
    "chargetime_accel",

    # Physical interaction and thermal efficiency ratios
    "thermal_dissipation_rate",
    "charge_efficiency_proxy",
    "resistance_growth_ratio",

    # Past-only historical rolling statistics (window=5 cycles)
    "IR_roll_mean_5",
    "IR_roll_std_5",
    "QCharge_roll_mean_5",
    "QCharge_roll_std_5",
    "Tavg_roll_mean_5",
    "Tavg_roll_std_5",

    # Early-life cumulative degradation rates
    "cum_capacity_fade_rate",
    "cum_resistance_growth_rate"
]

# 3. Canonical 32 Causal Feature Schema for Locked Advanced Models
ADVANCED_FEATURE_COLUMNS: List[str] = BASELINE_FEATURE_COLUMNS + CANDIDATE_CAUSAL_FEATURES
assert len(ADVANCED_FEATURE_COLUMNS) == 32, "ADVANCED_FEATURE_COLUMNS must contain exactly 32 features"

# 4. Feature Groups for Interpretability & Decomposition
FEATURE_GROUPS: Dict[str, List[str]] = {
    "Raw Physical Measurements": [
        "IR", "QCharge", "Tavg", "Tmax", "Tmin", "chargetime"
    ],
    "Temporal / Cycle Dynamics": [
        "cycle"
    ],
    "First-Order Lags": [
        "IR_lag1", "QCharge_lag1", "Tavg_lag1", "chargetime_lag1"
    ],
    "Delta & Second-Order Acceleration": [
        "IR_delta", "QCharge_delta", "Tavg_delta", "chargetime_delta",
        "IR_accel", "QCharge_accel", "Tavg_accel", "chargetime_accel"
    ],
    "Historical Rolling & Cumulative Trajectory": [
        "thermal_dissipation_rate", "charge_efficiency_proxy", "resistance_growth_ratio",
        "IR_roll_mean_5", "IR_roll_std_5", "QCharge_roll_mean_5", "QCharge_roll_std_5",
        "Tavg_roll_mean_5", "Tavg_roll_std_5", "cum_capacity_fade_rate", "cum_resistance_growth_rate"
    ],
    "Anomaly & Sensor Fault Indicators": [
        "IR_is_zero", "temp_sensor_fault"
    ]
}

# 5. Forbidden Target Leakage & Metadata Columns
FORBIDDEN_COLUMNS: List[str] = [
    "QDischarge",              # Direct target leakage with SOH (r = 0.9989)
    "max_cycle",               # Future lifespan leakage
    "final_cycle",             # Future lifespan leakage
    "terminal_cycle",          # Future lifespan leakage
    "total_cycles",            # Future lifespan leakage
    "future_observations"      # Future lookahead
]

# Target-specific forbidden columns
FORBIDDEN_SOH_COLUMNS: List[str] = FORBIDDEN_COLUMNS + ["SOH", "RUL", "predicted_soh"]
FORBIDDEN_RUL_COLUMNS: List[str] = FORBIDDEN_COLUMNS + ["SOH", "RUL", "predicted_rul"]

# Grouping and non-predictive metadata columns
METADATA_COLUMNS: List[str] = [
    "battery_id",
    "cycle",
    "row_id",
    "timestamp"
]

# 6. Physical Admissibility Bounds for Sensor Inputs
# Values outside these bounds indicate corrupt data or faulty sensors.
PHYSICAL_VALUE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "cycle": (1.0, 10000.0),
    "IR": (0.0, 10.0),                 # Internal resistance in Ohms
    "QCharge": (0.0, 20.0),             # Charge capacity in Ah
    "Tavg": (-20.0, 100.0),            # Average temperature in deg C
    "Tmax": (-20.0, 120.0),            # Max temperature in deg C
    "Tmin": (-30.0, 100.0),            # Min temperature in deg C
    "chargetime": (0.0, 5000.0),       # Charge time in minutes / arbitrary units
    "IR_is_zero": (0.0, 1.0),
    "temp_sensor_fault": (0.0, 1.0)
}
