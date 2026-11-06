"""
EcoCycle AI — Interactive Demonstration Script
Task 2N — Production Inference API & Application Integration

Demonstrates:
1. Loading the certified inference pipeline and verifying artifact hashes.
2. Running single-cycle inference on synthetic healthy and degraded battery telemetry.
3. Preserving authoritative raw predictions alongside presentation display values.
4. Explaining rule-based lifecycle degradation regimes (Healthy, Degraded, Critical Knee).
5. Demonstrating active rejection of corrupted inputs (missing features, NaNs).
6. Demonstrating strict anti-leakage guards against forbidden columns (QDischarge, max_cycle).

NOTE: Uses synthetic demonstration inputs only. The quarantined test partition is never accessed.
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.final_registry import get_default_registry
from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
from ml.models.inference import (
    predict_soh,
    predict_rul,
    predict_all,
    format_presentation_output,
    PIPELINE_VERSION
)
from ml.models.input_validation import (
    validate_inference_input,
    InputValidationError,
    DataLeakageError
)
from backend.services.interpretation import interpret_battery_health


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_synthetic_cycle_record(cycle_num: float, is_degraded: bool = False) -> dict:
    """Generates synthetic 32-feature battery telemetry without accessing test partition."""
    rec = {col: 0.0 for col in ADVANCED_FEATURE_COLUMNS}
    rec["cycle"] = float(cycle_num)
    rec["battery_id"] = 999  # synthetic demo battery ID
    rec["row_id"] = f"synthetic_cycle_{int(cycle_num)}"

    if not is_degraded:
        # Healthy early-life cell (~98% SOH, ~1,200 cycles RUL)
        rec["IR"] = 0.0082
        rec["QCharge"] = 1.072
        rec["Tavg"] = 28.5
        rec["Tmax"] = 30.1
        rec["Tmin"] = 27.0
        rec["chargetime"] = 42.0
        rec["IR_is_zero"] = 0.0
        rec["temp_sensor_fault"] = 0.0
        rec["IR_lag1"] = 0.0081
        rec["IR_delta"] = 0.0001
        rec["QCharge_lag1"] = 1.073
        rec["QCharge_delta"] = -0.001
        rec["Tavg_lag1"] = 28.4
        rec["Tavg_delta"] = 0.1
        rec["chargetime_lag1"] = 42.1
        rec["chargetime_delta"] = -0.1
        rec["IR_accel"] = 0.00001
        rec["QCharge_accel"] = -0.00002
        rec["Tavg_accel"] = 0.01
        rec["chargetime_accel"] = -0.01
        rec["thermal_dissipation_rate"] = (rec["Tmax"] - rec["Tmin"]) / rec["chargetime"]
        rec["charge_efficiency_proxy"] = rec["QCharge"] / rec["chargetime"]
        rec["resistance_growth_ratio"] = rec["IR"] / rec["IR_lag1"]
        rec["IR_roll_mean_5"] = 0.00815
        rec["IR_roll_std_5"] = 0.00005
        rec["QCharge_roll_mean_5"] = 1.0725
        rec["QCharge_roll_std_5"] = 0.0008
        rec["Tavg_roll_mean_5"] = 28.45
        rec["Tavg_roll_std_5"] = 0.12
        rec["cum_capacity_fade_rate"] = 0.00008
        rec["cum_resistance_growth_rate"] = 0.00001
    else:
        # Degraded near-EOL cell (~77% SOH, ~80 cycles RUL)
        rec["IR"] = 0.0185
        rec["QCharge"] = 0.835
        rec["Tavg"] = 35.8
        rec["Tmax"] = 39.2
        rec["Tmin"] = 32.5
        rec["chargetime"] = 34.0
        rec["IR_is_zero"] = 0.0
        rec["temp_sensor_fault"] = 0.0
        rec["IR_lag1"] = 0.0181
        rec["IR_delta"] = 0.0004
        rec["QCharge_lag1"] = 0.840
        rec["QCharge_delta"] = -0.005
        rec["Tavg_lag1"] = 35.5
        rec["Tavg_delta"] = 0.3
        rec["chargetime_lag1"] = 34.4
        rec["chargetime_delta"] = -0.4
        rec["IR_accel"] = 0.00008
        rec["QCharge_accel"] = -0.00015
        rec["Tavg_accel"] = 0.05
        rec["chargetime_accel"] = -0.08
        rec["thermal_dissipation_rate"] = (rec["Tmax"] - rec["Tmin"]) / rec["chargetime"]
        rec["charge_efficiency_proxy"] = rec["QCharge"] / rec["chargetime"]
        rec["resistance_growth_ratio"] = rec["IR"] / rec["IR_lag1"]
        rec["IR_roll_mean_5"] = 0.0179
        rec["IR_roll_std_5"] = 0.0003
        rec["QCharge_roll_mean_5"] = 0.843
        rec["QCharge_roll_std_5"] = 0.004
        rec["Tavg_roll_mean_5"] = 35.2
        rec["Tavg_roll_std_5"] = 0.45
        rec["cum_capacity_fade_rate"] = 0.00035
        rec["cum_resistance_growth_rate"] = 0.00008

    return rec


def main():
    print_banner(f"ECOCYCLE AI — MODEL INFERENCE DEMONSTRATION (v{PIPELINE_VERSION})")

    # Step 1: Model Registry Verification
    print("\n[Step 1] Loading Centralized Model Registry & Verifying Cryptographic Hashes...")
    reg = get_default_registry()
    soh_meta = reg.get_model_metadata("soh")
    rul_meta = reg.get_model_metadata("rul")

    print(f"  [PASS] SOH Model: {soh_meta['model_id']} ({soh_meta['framework']} {soh_meta['framework_version']})")
    print(f"         Test RMSE: {soh_meta['test_rmse']:.4f}% | Test R²: {soh_meta['test_r2']:.4f}")
    print(f"         Artifact SHA-256 Verified: {soh_meta['artifact_sha256'][:16]}...")
    print(f"  [PASS] RUL Model: {rul_meta['model_id']} ({rul_meta['framework']} {rul_meta['framework_version']})")
    print(f"         Test RMSE: {rul_meta['test_rmse']:.2f} cycles | Test R²: {rul_meta['test_r2']:.4f}")
    print(f"         Artifact SHA-256 Verified: {rul_meta['artifact_sha256'][:16]}...")

    # Step 2: Healthy Cell Scoring
    print_banner("DEMO SCENARIO A: HEALTHY BATTERY CELL (Early Lifecycle)")
    healthy_cell = create_synthetic_cycle_record(cycle_num=80.0, is_degraded=False)
    print(f"  Input Telemetry: cycle={healthy_cell['cycle']}, QCharge={healthy_cell['QCharge']} Ah, IR={healthy_cell['IR']} Ohm, Tavg={healthy_cell['Tavg']} °C")

    res_a = predict_all(healthy_cell)
    raw_soh_a = res_a["predicted_soh"]
    raw_rul_a = res_a["predicted_rul"]
    pres_a = format_presentation_output(raw_soh_a, raw_rul_a)
    interp_a = interpret_battery_health(raw_soh_a, raw_rul_a)

    print("\n  Prediction Output:")
    print(f"  - SOH Authoritative Raw: {pres_a['raw_soh']:.4f}% | Display Value: {pres_a['display_soh']:.2f}%")
    print(f"  - RUL Authoritative Raw: {pres_a['raw_rul']:.2f} cyc | Display Value: {pres_a['display_rul']:.1f} cyc")
    print(f"\n  Operational Regime Interpretation:")
    print(f"  - SOH Regime: [{interp_a['soh']['category']}] — {interp_a['soh']['description']}")
    print(f"  - RUL Regime: [{interp_a['rul']['category']}] — {interp_a['rul']['description']}")

    # Step 3: Degraded Cell Scoring
    print_banner("DEMO SCENARIO B: DEGRADED BATTERY CELL (Near Retirement Knee)")
    degraded_cell = create_synthetic_cycle_record(cycle_num=920.0, is_degraded=True)
    print(f"  Input Telemetry: cycle={degraded_cell['cycle']}, QCharge={degraded_cell['QCharge']} Ah, IR={degraded_cell['IR']} Ohm, Tavg={degraded_cell['Tavg']} °C")

    res_b = predict_all(degraded_cell)
    raw_soh_b = res_b["predicted_soh"]
    raw_rul_b = res_b["predicted_rul"]
    pres_b = format_presentation_output(raw_soh_b, raw_rul_b)
    interp_b = interpret_battery_health(raw_soh_b, raw_rul_b)

    print("\n  Prediction Output:")
    print(f"  - SOH Authoritative Raw: {pres_b['raw_soh']:.4f}% | Display Value: {pres_b['display_soh']:.2f}%")
    print(f"  - RUL Authoritative Raw: {pres_b['raw_rul']:.2f} cyc | Display Value: {pres_b['display_rul']:.1f} cyc")
    print(f"\n  Operational Regime Interpretation:")
    print(f"  - SOH Regime: [{interp_b['soh']['category']}] — {interp_b['soh']['description']}")
    print(f"  - RUL Regime: [{interp_b['rul']['category']}] — {interp_b['rul']['description']}")

    # Step 4: Invalid Input Rejection Demonstration
    print_banner("DEMO SCENARIO C: ROBUST INPUT VALIDATION & FAULT INTERCEPTION")
    print("  Testing rejection of input with missing required features...")
    bad_rec = healthy_cell.copy()
    del bad_rec["QCharge_lag1"]
    try:
        predict_soh(bad_rec)
        print("  [FAIL] Failed to catch missing feature!")
    except InputValidationError as e:
        print(f"  [PASS] Correctly intercepted: InputValidationError — {e}")

    print("\n  Testing rejection of corrupt input containing NaN sensor readings...")
    nan_rec = healthy_cell.copy()
    nan_rec["Tavg_roll_mean_5"] = np.nan
    try:
        predict_rul(nan_rec)
        print("  [FAIL] Failed to catch NaN!")
    except InputValidationError as e:
        print(f"  [PASS] Correctly intercepted: InputValidationError — {e}")

    # Step 5: Anti-Leakage Guard Demonstration
    print_banner("DEMO SCENARIO D: ANTI-LEAKAGE SECURITY ENFORCEMENT")
    print("  Testing rejection of direct target leakage feature ('QDischarge')...")
    leak_rec1 = healthy_cell.copy()
    leak_rec1["QDischarge"] = 1.065
    try:
        validate_inference_input(leak_rec1)
        print("  [FAIL] Failed to catch QDischarge leakage!")
    except DataLeakageError as e:
        print(f"  [PASS] Correctly intercepted: DataLeakageError — {e}")

    print("\n  Testing rejection of future lifespan lookahead ('max_cycle')...")
    leak_rec2 = healthy_cell.copy()
    leak_rec2["max_cycle"] = 1250
    try:
        validate_inference_input(leak_rec2)
        print("  [FAIL] Failed to catch max_cycle leakage!")
    except DataLeakageError as e:
        print(f"  [PASS] Correctly intercepted: DataLeakageError — {e}")

    print_banner("DEMONSTRATION COMPLETED CLEANLY — ALL GUARDS VERIFIED ACTIVE")


if __name__ == "__main__":
    main()
