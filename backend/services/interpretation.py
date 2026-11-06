"""
EcoCycle AI — Battery Degradation Interpretation Service
Task 2N — Production Inference API & Application Integration

Provides deterministic, rule-based interpretation of SOH and RUL model outputs.
IMPORTANT: These categories represent presentation/business demonstration rules
established during Task 2L.3 and Task 2N diagnostic audits. They are NOT
scientifically validated medical or industrial guarantees.
"""

from typing import Dict, Any


def interpret_soh(soh_val: float) -> Dict[str, str]:
    """
    Categorizes SOH prediction into documented lifecycle degradation regimes.
    Thresholds correspond to Task 2L.3 and Task 2N empirical benchmarks:
    - >= 90%: Normal Aging / Healthy
    - 80% - 90%: Degraded Subpopulation
    - < 80%: Critical Knee Regime
    """
    if soh_val >= 90.0:
        return {
            "category": "Healthy (Normal Aging)",
            "description": "Capacity retention is at or above 90%. Battery is in a healthy, linear aging stage.",
            "confidence_note": "High predictive precision (MAE ~0.30%). Suitable for all primary operational demands."
        }
    elif soh_val >= 80.0:
        return {
            "category": "Degraded Subpopulation",
            "description": "Capacity retention is between 80% and 90%. Cell is approaching the degradation knee transition.",
            "confidence_note": "Moderate variance across battery cells (MAE ~0.83%). Regular diagnostic surveillance recommended."
        }
    else:
        return {
            "category": "Critical Knee Regime",
            "description": "Capacity retention has dropped below 80% (nominal end-of-first-life threshold).",
            "confidence_note": "Rapid non-linear capacity fade occurs in this regime. Cell should be retired or repurposed for secondary stationary storage."
        }


def interpret_rul(rul_val: float) -> Dict[str, str]:
    """
    Categorizes RUL prediction into documented lifecycle operational regimes.
    Thresholds correspond to Task 2L.3 and Task 2N empirical benchmarks:
    - >= 800 cycles: Early-Life / Long Remaining Life
    - 300 - 800 cycles: Mid-Life / Moderate Remaining Life
    - < 300 cycles: Near-End-of-Life / Retirement Proximity
    """
    if rul_val >= 800.0:
        return {
            "category": "Early-Life (Long Remaining Life)",
            "description": "Estimated remaining useful operational lifespan is 800 or more cycles.",
            "confidence_note": "Early-cycle variance is higher (MAE ~226 cyc) due to physical cell indistinguishability prior to degradation divergence."
        }
    elif rul_val >= 300.0:
        return {
            "category": "Mid-Life (Moderate Remaining Life)",
            "description": "Estimated remaining useful operational lifespan is between 300 and 800 cycles.",
            "confidence_note": "Reliable trajectory tracking by CatBoost 32f (MAE ~116 cyc). Normal maintenance schedule applies."
        }
    else:
        return {
            "category": "Near-End-of-Life (Retirement Proximity)",
            "description": "Estimated remaining useful operational lifespan is under 300 cycles.",
            "confidence_note": "High operational precision (MAE ~66 cyc, RMSE < 100 cyc). Provides safe advance notice for cell replacement."
        }


def interpret_battery_health(soh_val: float, rul_val: float) -> Dict[str, Dict[str, str]]:
    """Combines SOH and RUL interpretations with provenance attribution."""
    return {
        "soh": interpret_soh(soh_val),
        "rul": interpret_rul(rul_val)
    }
