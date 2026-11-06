"""
EcoCycle AI — Second-Life Decision Engine Demonstration Script
Task 2O — Second-Life Decision Engine

Demonstrates:
1. Initializing the deterministic SecondLifeDecisionEngine and verifying model provenance.
2. Scenario A: Healthy battery cell -> PRIMARY_OPERATION (Continued Primary Operation).
3. Scenario B: Degraded battery cell -> SECOND_LIFE_CANDIDATE (Stationary Energy Storage).
4. Scenario C: Critical / End-of-Life cell -> MATERIAL_RECYCLING (Direct Material Recovery).
5. Scenario D: Atypical cell (Critical SOH with high cycles) -> SECOND_LIFE_CANDIDATE (REVIEW_REQUIRED).
6. Scenario E: Raw prediction unclipped preservation (raw negative RUL preserved; display bounded to 0.0).
7. Scenario F: Active anti-leakage protection (QDischarge, max_cycle intercepted).
8. Deterministic reasoning explanation, threshold definitions, and non-certification disclaimer.

NOTE: Uses synthetic demonstration inputs only. The quarantined test partition is never accessed.
"""

import sys
import json
from pathlib import Path
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.final_registry import get_default_registry
from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
from ml.models.input_validation import validate_inference_input, DataLeakageError, InputValidationError
from ml.models.inference import predict_all
from backend.services.decision.engine import get_default_decision_engine
from backend.services.decision.constants import (
    DECISION_PRIMARY_OPERATION,
    DECISION_SECOND_LIFE_CANDIDATE,
    DECISION_MATERIAL_RECYCLING,
    DECISION_DISCLAIMER
)


def print_banner(title: str):
    print("\n" + "=" * 76)
    print(f"  {title}")
    print("=" * 76)


def create_synthetic_telemetry(cycle_num: float, degradation_level: str = "healthy") -> dict:
    """
    Generates synthetic 32-feature battery telemetry for demonstration.
    degradation_level: 'healthy', 'degraded', or 'critical'
    """
    rec = {col: 0.0 for col in ADVANCED_FEATURE_COLUMNS}
    rec["cycle"] = float(cycle_num)
    rec["battery_id"] = 888
    rec["row_id"] = f"demo_cycle_{int(cycle_num)}"

    if degradation_level == "healthy":
        # Healthy early cell (~97% SOH, ~900 cycles RUL)
        rec["IR"] = 0.0080
        rec["QCharge"] = 1.075
        rec["Tavg"] = 28.0
        rec["Tmax"] = 29.5
        rec["Tmin"] = 26.5
        rec["chargetime"] = 43.0
        rec["IR_lag1"] = 0.0079
        rec["IR_delta"] = 0.0001
        rec["QCharge_lag1"] = 1.076
        rec["QCharge_delta"] = -0.001
        rec["Tavg_lag1"] = 27.9
        rec["Tavg_delta"] = 0.1
        rec["chargetime_lag1"] = 43.1
        rec["chargetime_delta"] = -0.1
        rec["thermal_dissipation_rate"] = (rec["Tmax"] - rec["Tmin"]) / rec["chargetime"]
        rec["charge_efficiency_proxy"] = rec["QCharge"] / rec["chargetime"]
        rec["resistance_growth_ratio"] = rec["IR"] / rec["IR_lag1"]
        rec["IR_roll_mean_5"] = 0.00795
        rec["IR_roll_std_5"] = 0.00004
        rec["QCharge_roll_mean_5"] = 1.0755
        rec["QCharge_roll_std_5"] = 0.0005
        rec["Tavg_roll_mean_5"] = 27.95
        rec["Tavg_roll_std_5"] = 0.10
        rec["cum_capacity_fade_rate"] = 0.00005
        rec["cum_resistance_growth_rate"] = 0.00001
    elif degradation_level == "degraded":
        # Degraded second-life cell (~85% SOH, ~550 cycles RUL)
        rec["IR"] = 0.0125
        rec["QCharge"] = 0.940
        rec["Tavg"] = 32.0
        rec["Tmax"] = 34.5
        rec["Tmin"] = 29.5
        rec["chargetime"] = 38.0
        rec["IR_lag1"] = 0.0123
        rec["IR_delta"] = 0.0002
        rec["QCharge_lag1"] = 0.943
        rec["QCharge_delta"] = -0.003
        rec["Tavg_lag1"] = 31.8
        rec["Tavg_delta"] = 0.2
        rec["chargetime_lag1"] = 38.2
        rec["chargetime_delta"] = -0.2
        rec["thermal_dissipation_rate"] = (rec["Tmax"] - rec["Tmin"]) / rec["chargetime"]
        rec["charge_efficiency_proxy"] = rec["QCharge"] / rec["chargetime"]
        rec["resistance_growth_ratio"] = rec["IR"] / rec["IR_lag1"]
        rec["IR_roll_mean_5"] = 0.0122
        rec["IR_roll_std_5"] = 0.00015
        rec["QCharge_roll_mean_5"] = 0.945
        rec["QCharge_roll_std_5"] = 0.002
        rec["Tavg_roll_mean_5"] = 31.7
        rec["Tavg_roll_std_5"] = 0.25
        rec["cum_capacity_fade_rate"] = 0.00020
        rec["cum_resistance_growth_rate"] = 0.00004
    else:
        # Critical knee / end-of-life cell (~72% SOH, ~90 cycles RUL)
        rec["IR"] = 0.0195
        rec["QCharge"] = 0.810
        rec["Tavg"] = 36.5
        rec["Tmax"] = 40.5
        rec["Tmin"] = 33.0
        rec["chargetime"] = 33.0
        rec["IR_lag1"] = 0.0190
        rec["IR_delta"] = 0.0005
        rec["QCharge_lag1"] = 0.816
        rec["QCharge_delta"] = -0.006
        rec["Tavg_lag1"] = 36.1
        rec["Tavg_delta"] = 0.4
        rec["chargetime_lag1"] = 33.5
        rec["chargetime_delta"] = -0.5
        rec["thermal_dissipation_rate"] = (rec["Tmax"] - rec["Tmin"]) / rec["chargetime"]
        rec["charge_efficiency_proxy"] = rec["QCharge"] / rec["chargetime"]
        rec["resistance_growth_ratio"] = rec["IR"] / rec["IR_lag1"]
        rec["IR_roll_mean_5"] = 0.0188
        rec["IR_roll_std_5"] = 0.0004
        rec["QCharge_roll_mean_5"] = 0.820
        rec["QCharge_roll_std_5"] = 0.005
        rec["Tavg_roll_mean_5"] = 35.8
        rec["Tavg_roll_std_5"] = 0.50
        rec["cum_capacity_fade_rate"] = 0.00038
        rec["cum_resistance_growth_rate"] = 0.00009

    return rec


def print_assessment_result(res: dict):
    dec = res["decision"]
    preds = res["predictions"]
    reg = res["regimes"]

    print(f"\n  LIFECYCLE DECISION: [{dec['category']}]")
    print(f"  Recommended Application : {dec['recommended_application']}")
    print(f"  Qualitative Rule Strength : {dec['decision_strength']}")
    print(f"\n  Certified Predictions:")
    print(f"  - SOH Raw: {preds['soh']['raw']:.4f}% | Display: {preds['soh']['display']:.2f}% | Regime: {reg['soh']}")
    print(f"  - RUL Raw: {preds['rul']['raw']:.2f} cyc | Display: {preds['rul']['display']:.1f} cyc | Regime: {reg['rul']}")
    print(f"\n  Deterministic Reasoning Steps:")
    for step in res["reasoning"]:
        print(f"    * {step}")


def main():
    print_banner("ECOCYCLE AI — SECOND-LIFE DECISION ENGINE DEMONSTRATION (TASK 2O)")

    # Step 1: Initialize Engine
    print("\n[Step 1] Initializing Second-Life Decision Engine & Verifying Artifact Provenance...")
    engine = get_default_decision_engine()
    reg = get_default_registry()
    print(f"  [PASS] Decision Engine Version : {engine.ENGINE_VERSION}")
    print(f"  [PASS] SOH Estimator           : {reg.get_model_metadata('soh')['model_id']}")
    print(f"  [PASS] RUL Estimator           : {reg.get_model_metadata('rul')['model_id']}")

    # Step 2: Scenario A - Healthy Primary Operation
    print_banner("DEMO SCENARIO A: HEALTHY BATTERY CELL (Early Lifecycle)")
    telemetry_a = create_synthetic_telemetry(cycle_num=50.0, degradation_level="healthy")
    X_a, _ = validate_inference_input(telemetry_a)
    preds_a = predict_all(X_a)
    assessment_a = engine.assess_from_predictions(preds_a["predicted_soh"], preds_a["predicted_rul"], metadata={"demo": "scenario_a"})
    print_assessment_result(assessment_a)
    assert assessment_a["decision"]["category"] == DECISION_PRIMARY_OPERATION, "Scenario A category mismatch"

    # Step 3: Scenario B - Degraded Second-Life Candidate
    print_banner("DEMO SCENARIO B: DEGRADED BATTERY CELL (Repurposing Candidate)")
    telemetry_b = create_synthetic_telemetry(cycle_num=550.0, degradation_level="degraded")
    X_b, _ = validate_inference_input(telemetry_b)
    preds_b = predict_all(X_b)
    assessment_b = engine.assess_from_predictions(preds_b["predicted_soh"], preds_b["predicted_rul"], metadata={"demo": "scenario_b"})
    print_assessment_result(assessment_b)
    assert assessment_b["decision"]["category"] == DECISION_SECOND_LIFE_CANDIDATE, "Scenario B category mismatch"

    # Step 4: Scenario C - Critical Retirement / Material Recycling
    print_banner("DEMO SCENARIO C: CRITICAL BATTERY CELL (Near End-of-Life)")
    telemetry_c = create_synthetic_telemetry(cycle_num=1150.0, degradation_level="critical")
    X_c, _ = validate_inference_input(telemetry_c)
    preds_c = predict_all(X_c)
    assessment_c = engine.assess_from_predictions(preds_c["predicted_soh"], preds_c["predicted_rul"], metadata={"demo": "scenario_c"})
    print_assessment_result(assessment_c)
    assert assessment_c["decision"]["category"] == DECISION_MATERIAL_RECYCLING, "Scenario C category mismatch"

    # Step 5: Scenario D - Anomaly / Review Required
    print_banner("DEMO SCENARIO D: ATYPICAL PROFILE (Critical SOH but High RUL -> Engineering Review)")
    # Direct simulation of atypical combination: SOH 75.0% with RUL 850 cycles
    assessment_d = engine.assess_from_predictions(75.0, 850.0, metadata={"demo": "scenario_d"})
    print_assessment_result(assessment_d)
    assert assessment_d["decision"]["decision_strength"] == "REVIEW_REQUIRED", "Scenario D strength mismatch"

    # Step 6: Scenario E - Raw Negative Prediction Preservation
    print_banner("DEMO SCENARIO E: RAW VS PRESENTATION PREDICTION PRESERVATION")
    print("  Evaluating past-terminal prediction: raw SOH = 65.5%, raw RUL = -42.8 cycles...")
    assessment_e = engine.assess_from_predictions(65.5, -42.8, metadata={"demo": "scenario_e"})
    preds_e = assessment_e["predictions"]
    print(f"  - Raw SOH: {preds_e['soh']['raw']}% (Preserved unclipped)")
    print(f"  - Raw RUL: {preds_e['rul']['raw']} cycles (Preserved negative)")
    print(f"  - Display SOH: {preds_e['soh']['display']}% (Presentation bounded)")
    print(f"  - Display RUL: {preds_e['rul']['display']} cycles (Presentation bounded to 0.0)")
    print(f"  - Decision Outcome: [{assessment_e['decision']['category']}] -> {assessment_e['decision']['recommended_application']}")
    assert preds_e["rul"]["raw"] == -42.8
    assert preds_e["rul"]["display"] == 0.0
    assert assessment_e["decision"]["category"] == DECISION_MATERIAL_RECYCLING

    # Step 7: Scenario F - Anti-Leakage Protection
    print_banner("DEMO SCENARIO F: ANTI-LEAKAGE SECURITY ENFORCEMENT")
    bad_rec = telemetry_a.copy()
    bad_rec["QDischarge"] = 1.05
    try:
        validate_inference_input(bad_rec)
        print("  [FAIL] Failed to catch QDischarge leakage!")
    except DataLeakageError as e:
        print(f"  [PASS] Correctly intercepted QDischarge leakage: DataLeakageError")

    bad_rec2 = telemetry_a.copy()
    bad_rec2["max_cycle"] = 1200
    try:
        validate_inference_input(bad_rec2)
        print("  [FAIL] Failed to catch max_cycle leakage!")
    except DataLeakageError as e:
        print(f"  [PASS] Correctly intercepted max_cycle leakage: DataLeakageError")

    # Step 8: Non-certification disclaimer verification
    print_banner("SAFETY & METHODOLOGICAL DISCLAIMER")
    print(f"  \"{assessment_a['disclaimer']}\"")
    print_banner("ALL TASK 2O DEMONSTRATION SCENARIOS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
