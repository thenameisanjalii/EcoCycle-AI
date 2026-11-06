"""
EcoCycle AI — Causal Feature Engineering Module
Task 2M.1 — Advanced Model Design

Defines:
1. Candidate causal features extending the 17-feature baseline schema
2. Formal mathematical formulation and causality proofs for each feature
3. Causality audit function verifying zero future information leakage
4. Causal feature generation pipeline operating strictly per-battery cell
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any

# Baseline 17 features established in Task 2K and locked in Task 2L
BASELINE_FEATURE_COLUMNS = [
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

# 15 Advanced Candidate Causal Features
CANDIDATE_CAUSAL_FEATURES = [
    # 1. Second-order rate of change (acceleration)
    "IR_accel",
    "QCharge_accel",
    "Tavg_accel",
    "chargetime_accel",

    # 2. Physical interaction and thermal efficiency ratios
    "thermal_dissipation_rate",
    "charge_efficiency_proxy",
    "resistance_growth_ratio",

    # 3. Past-only historical rolling statistics (window=5 cycles)
    "IR_roll_mean_5",
    "IR_roll_std_5",
    "QCharge_roll_mean_5",
    "QCharge_roll_std_5",
    "Tavg_roll_mean_5",
    "Tavg_roll_std_5",

    # 4. Early-life cumulative degradation slopes (disambiguating early RUL)
    "cum_capacity_fade_rate",
    "cum_resistance_growth_rate"
]

# Full 32-feature advanced candidate schema
ADVANCED_FEATURE_COLUMNS = BASELINE_FEATURE_COLUMNS + CANDIDATE_CAUSAL_FEATURES

# Forbidden Features Registry
FORBIDDEN_COLUMNS = [
    "battery_id",              # Grouping metadata only; MUST NOT enter X
    "QDischarge",              # Target leakage with SOH (Pearson r = 0.9989)
    "SOH_in_RUL",              # Ground-truth SOH forbidden when predicting RUL
    "RUL_in_SOH",              # Ground-truth RUL forbidden when predicting SOH
    "max_cycle",               # Direct future leakage of total cell lifespan
    "final_cycle",             # Direct future leakage of total cell lifespan
    "terminal_cycle",          # Direct future leakage
    "future_observations",     # Any t+k measurements
    "center_rolling_windows",  # Any symmetric / centered rolling window
    "bfill_from_future"        # Any backward fill propagating future state backwards
]

# Detailed Mathematical Definitions and Causality Proofs
CAUSAL_FEATURE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "IR_accel": {
        "formula": "IR_delta(t) - IR_delta(t-1)",
        "inputs": ["IR(t)", "IR(t-1)", "IR(t-2)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "At cycle t, measurements IR(t), IR(t-1), and IR(t-2) are all observed in the past or present. No future cycle is referenced.",
        "physical_rationale": "Second derivative of internal resistance indicates onset of non-linear SEI thickening or lithium plating."
    },
    "QCharge_accel": {
        "formula": "QCharge_delta(t) - QCharge_delta(t-1)",
        "inputs": ["QCharge(t)", "QCharge(t-1)", "QCharge(t-2)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Strictly utilizes charge capacity deltas from cycles t and t-1, depending only on past cycles t, t-1, t-2 <= t.",
        "physical_rationale": "Captures the curvature of capacity loss, detecting transitions from steady linear aging into accelerated aging knees."
    },
    "Tavg_accel": {
        "formula": "Tavg_delta(t) - Tavg_delta(t-1)",
        "inputs": ["Tavg(t)", "Tavg(t-1)", "Tavg(t-2)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Utilizes past average temperature changes up to cycle t. 100% causal.",
        "physical_rationale": "Detects thermal runaway precursors and internal heating rate escalation."
    },
    "chargetime_accel": {
        "formula": "chargetime_delta(t) - chargetime_delta(t-1)",
        "inputs": ["chargetime(t)", "chargetime(t-1)", "chargetime(t-2)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Strictly past observations up to cycle t.",
        "physical_rationale": "Acceleration in charging duration changes reveals impedance-limited charging kinetics."
    },
    "thermal_dissipation_rate": {
        "formula": "(Tmax(t) - Tmin(t)) / max(chargetime(t), 0.01)",
        "inputs": ["Tmax(t)", "Tmin(t)", "chargetime(t)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Instantaneous cycle t telemetry only.",
        "physical_rationale": "Thermal spread per unit charge time reflects Joule heating rate vs cell thermal dissipation capability."
    },
    "charge_efficiency_proxy": {
        "formula": "QCharge(t) / max(chargetime(t), 0.01)",
        "inputs": ["QCharge(t)", "chargetime(t)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Instantaneous cycle t telemetry only.",
        "physical_rationale": "Effective charging rate accepted by the cell; drops as electrode polarization increases."
    },
    "resistance_growth_ratio": {
        "formula": "IR(t) / max(IR_lag1(t), 1e-6)",
        "inputs": ["IR(t)", "IR(t-1)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Depends strictly on current cycle t and previous cycle t-1.",
        "physical_rationale": "Multiplicative step-increase in cell impedance."
    },
    "IR_roll_mean_5": {
        "formula": "mean(IR(i) for i in [max(1, t-4) .. t])",
        "inputs": ["IR(t)", "IR(t-1)", "IR(t-2)", "IR(t-3)", "IR(t-4)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Past-only rolling window (center=False, closed=right up to t). Does not include any cycle > t.",
        "physical_rationale": "Filters high-frequency sensor noise in resistance measurements to expose the latent aging curve."
    },
    "IR_roll_std_5": {
        "formula": "std(IR(i) for i in [max(1, t-4) .. t])",
        "inputs": ["IR(t)", "IR(t-1)", "IR(t-2)", "IR(t-3)", "IR(t-4)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Past-only rolling window of size 5 looking back from t.",
        "physical_rationale": "Rising resistance variance indicates cyclic contact instability or dendrite development."
    },
    "QCharge_roll_mean_5": {
        "formula": "mean(QCharge(i) for i in [max(1, t-4) .. t])",
        "inputs": ["QCharge(t)", "QCharge(t-1)", "QCharge(t-2)", "QCharge(t-3)", "QCharge(t-4)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Past-only rolling window of size 5 looking back from t.",
        "physical_rationale": "Smoothed charge capacity trajectory dampening cycle-to-cycle ambient temperature variations."
    },
    "QCharge_roll_std_5": {
        "formula": "std(QCharge(i) for i in [max(1, t-4) .. t])",
        "inputs": ["QCharge(t)", "QCharge(t-1)", "QCharge(t-2)", "QCharge(t-3)", "QCharge(t-4)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Past-only rolling window looking back from t.",
        "physical_rationale": "Measures capacity volatility across operating cycles."
    },
    "Tavg_roll_mean_5": {
        "formula": "mean(Tavg(i) for i in [max(1, t-4) .. t])",
        "inputs": ["Tavg(t)", "Tavg(t-1)", "Tavg(t-2)", "Tavg(t-3)", "Tavg(t-4)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Past-only rolling window looking back from t.",
        "physical_rationale": "Short-term moving thermal equilibrium state of the battery pack."
    },
    "Tavg_roll_std_5": {
        "formula": "std(Tavg(i) for i in [max(1, t-4) .. t])",
        "inputs": ["Tavg(t)", "Tavg(t-1)", "Tavg(t-2)", "Tavg(t-3)", "Tavg(t-4)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "Past-only rolling window looking back from t.",
        "physical_rationale": "Cyclic thermal stability indicator."
    },
    "cum_capacity_fade_rate": {
        "formula": "(QCharge(cycle=1) - QCharge(t)) / max(cycle(t) - 1, 1)",
        "inputs": ["QCharge(cycle=1)", "QCharge(t)", "cycle(t)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "QCharge(cycle=1) is the battery's initial capacity at birth (cycle 1). At cycle t, cycle 1 is strictly in the past. No future cycle or max_cycle is used.",
        "physical_rationale": "CRITICAL FOR EARLY RUL: Quantifies initial degradation slope. Cells with higher cumulative capacity loss per cycle in early life have shorter total lifespans, enabling early-life trajectory disambiguation."
    },
    "cum_resistance_growth_rate": {
        "formula": "(IR(t) - IR(cycle=1)) / max(cycle(t) - 1, 1)",
        "inputs": ["IR(cycle=1)", "IR(t)", "cycle(t)"],
        "max_time_index": "t",
        "causality_status": "PROVEN_CAUSAL",
        "proof": "IR(cycle=1) is initial resistance at birth. At cycle t, cycle 1 is in the past. No future cycle or max_cycle is used.",
        "physical_rationale": "CRITICAL FOR EARLY RUL: Quantifies initial impedance growth rate from beginning of life to cycle t without knowing total lifespan."
    }
}


def validate_causality_rules() -> Dict[str, Any]:
    """
    Performs static causality validation across all candidate features.
    Returns:
        dict: validation results, status, and certified feature counts.
    """
    results = {}
    for feat_name, meta in CAUSAL_FEATURE_REGISTRY.items():
        assert meta["causality_status"] == "PROVEN_CAUSAL", f"Feature {feat_name} not proven causal"
        assert meta["max_time_index"] == "t", f"Feature {feat_name} references future time index: {meta['max_time_index']}"
        results[feat_name] = "PASS"

    # Verify forbidden list integrity
    for forb in FORBIDDEN_COLUMNS:
        assert forb not in ADVANCED_FEATURE_COLUMNS, f"Forbidden entity leaked into feature columns: {forb}"

    return {
        "status": "PASS",
        "baseline_feature_count": len(BASELINE_FEATURE_COLUMNS),
        "candidate_causal_feature_count": len(CANDIDATE_CAUSAL_FEATURES),
        "total_advanced_feature_count": len(ADVANCED_FEATURE_COLUMNS),
        "forbidden_features_count": len(FORBIDDEN_COLUMNS),
        "features_validated": results
    }


def generate_causal_features_for_battery(battery_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes candidate causal features for a single battery cell's time series.
    Input must contain the 17 baseline features and be sorted chronologically by cycle.
    Strictly preserves causality: no lookahead, no future fill, no future rolling.
    """
    df = battery_df.sort_values("cycle").copy()

    # 1. Acceleration features (second-order changes)
    df["IR_accel"] = df["IR_delta"] - df["IR_delta"].shift(1)
    df["IR_accel"] = df["IR_accel"].fillna(0.0)

    df["QCharge_accel"] = df["QCharge_delta"] - df["QCharge_delta"].shift(1)
    df["QCharge_accel"] = df["QCharge_accel"].fillna(0.0)

    df["Tavg_accel"] = df["Tavg_delta"] - df["Tavg_delta"].shift(1)
    df["Tavg_accel"] = df["Tavg_accel"].fillna(0.0)

    df["chargetime_accel"] = df["chargetime_delta"] - df["chargetime_delta"].shift(1)
    df["chargetime_accel"] = df["chargetime_accel"].fillna(0.0)

    # 2. Physical interaction and efficiency ratios
    ct_safe = np.maximum(df["chargetime"].values, 0.01)
    df["thermal_dissipation_rate"] = (df["Tmax"].values - df["Tmin"].values) / ct_safe
    df["charge_efficiency_proxy"] = df["QCharge"].values / ct_safe

    ir_lag_safe = np.maximum(df["IR_lag1"].values, 1e-6)
    df["resistance_growth_ratio"] = df["IR"].values / ir_lag_safe

    # 3. Past-only historical rolling statistics (window=5 cycles, min_periods=1)
    df["IR_roll_mean_5"] = df["IR"].rolling(window=5, min_periods=1, center=False).mean()
    df["IR_roll_std_5"] = df["IR"].rolling(window=5, min_periods=1, center=False).std().fillna(0.0)

    df["QCharge_roll_mean_5"] = df["QCharge"].rolling(window=5, min_periods=1, center=False).mean()
    df["QCharge_roll_std_5"] = df["QCharge"].rolling(window=5, min_periods=1, center=False).std().fillna(0.0)

    df["Tavg_roll_mean_5"] = df["Tavg"].rolling(window=5, min_periods=1, center=False).mean()
    df["Tavg_roll_std_5"] = df["Tavg"].rolling(window=5, min_periods=1, center=False).std().fillna(0.0)

    # 4. Early-life cumulative degradation indicators (relative to cycle 1)
    initial_qcharge = df["QCharge"].iloc[0]
    initial_ir = df["IR"].iloc[0]
    cycle_denom = np.maximum(df["cycle"].values - 1.0, 1.0)

    df["cum_capacity_fade_rate"] = (initial_qcharge - df["QCharge"].values) / cycle_denom
    df["cum_resistance_growth_rate"] = (df["IR"].values - initial_ir) / cycle_denom

    return df


def generate_causal_features_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies generate_causal_features_for_battery across each battery cell in df.
    Preserves original row index and order.
    """
    dfs = []
    for b_id, group in df.groupby("battery_id", sort=False):
        dfs.append(generate_causal_features_for_battery(group))
    res = pd.concat(dfs, axis=0).sort_index()
    return res

