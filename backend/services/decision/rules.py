"""
EcoCycle AI — Deterministic Second-Life Decision Rules
Task 2O — Second-Life Decision Engine

Evaluates ML regression predictions (SOH and RUL) against project-defined
demonstration decision rules to produce a transparent lifecycle recommendation.
"""

from typing import Dict, Any, List, Tuple
from .constants import (
    SOH_HEALTHY_MIN,
    SOH_DEGRADED_MIN,
    RUL_EARLY_LIFE_MIN,
    RUL_MID_LIFE_MIN,
    SOH_REGIME_HEALTHY,
    SOH_REGIME_DEGRADED,
    SOH_REGIME_CRITICAL,
    RUL_REGIME_EARLY,
    RUL_REGIME_MID,
    RUL_REGIME_NEAR_EOL,
    DECISION_PRIMARY_OPERATION,
    DECISION_SECOND_LIFE_CANDIDATE,
    DECISION_MATERIAL_RECYCLING,
    APP_CONTINUED_PRIMARY,
    APP_STATIONARY_STORAGE,
    APP_LIGHT_DUTY_STORAGE,
    APP_MATERIAL_RECOVERY,
    STRENGTH_STRONG,
    STRENGTH_MODERATE,
    STRENGTH_REVIEW_REQUIRED,
    THRESHOLD_DEFINITIONS
)


def get_soh_regime(soh_val: float) -> str:
    """
    Determines SOH degradation regime based on project thresholds.
    - >= 90.0%: HEALTHY_NORMAL_AGING
    - 80.0% to 90.0%: DEGRADED_SECOND_LIFE_CANDIDATE
    - < 80.0%: CRITICAL_KNEE_PRIMARY_RETIREMENT
    """
    if soh_val >= SOH_HEALTHY_MIN:
        return SOH_REGIME_HEALTHY
    elif soh_val >= SOH_DEGRADED_MIN:
        return SOH_REGIME_DEGRADED
    else:
        return SOH_REGIME_CRITICAL


def get_rul_regime(rul_val: float) -> str:
    """
    Determines RUL operational regime based on project thresholds.
    - >= 800.0 cycles: EARLY_LIFE
    - 300.0 to 800.0 cycles: MID_LIFE
    - < 300.0 cycles: NEAR_END_OF_LIFE (including unclipped negative RUL)
    """
    if rul_val >= RUL_EARLY_LIFE_MIN:
        return RUL_REGIME_EARLY
    elif rul_val >= RUL_MID_LIFE_MIN:
        return RUL_REGIME_MID
    else:
        return RUL_REGIME_NEAR_EOL


def evaluate_second_life_decision(
    raw_soh: float,
    raw_rul: float,
    display_soh: float,
    display_rul: float
) -> Dict[str, Any]:
    """
    Evaluates dual-target predictions against the 6-case second-life decision matrix.

    CRITICAL PRINCIPLE:
    - Decisions are evaluated using authoritative raw predictions, with display values
      providing non-negative physical bounds for UI display.
    - Returns deterministic category, recommended application, decision strength,
      regimes, step-by-step reasoning, and rule definitions.

    Args:
        raw_soh: Authoritative SOH output from XGBoost model (%).
        raw_rul: Authoritative unclipped RUL output from CatBoost model (cycles).
        display_soh: Bounded SOH value (0-100%).
        display_rul: Bounded RUL value (>= 0 cycles).

    Returns:
        Dictionary structured for SecondLifeAssessmentResponse.
    """
    soh_regime = get_soh_regime(raw_soh)
    rul_regime = get_rul_regime(raw_rul)

    reasoning: List[str] = []

    # CASE 1: SOH >= 90% AND RUL >= 800 cycles
    if raw_soh >= SOH_HEALTHY_MIN and raw_rul >= RUL_EARLY_LIFE_MIN:
        category = DECISION_PRIMARY_OPERATION
        recommended_app = APP_CONTINUED_PRIMARY
        strength = STRENGTH_STRONG
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) is in the healthy aging regime (>={SOH_HEALTHY_MIN:.0f}%)."
        )
        reasoning.append(
            f"Predicted RUL ({raw_rul:.1f} cycles) indicates extensive remaining operational life (>={RUL_EARLY_LIFE_MIN:.0f} cycles)."
        )
        reasoning.append(
            "Battery remains fully suitable for continued primary operation without degradation-induced restriction."
        )

    # CASE 2: SOH >= 90% AND 300 <= RUL < 800 cycles
    elif raw_soh >= SOH_HEALTHY_MIN and raw_rul >= RUL_MID_LIFE_MIN:
        category = DECISION_PRIMARY_OPERATION
        recommended_app = APP_CONTINUED_PRIMARY
        strength = STRENGTH_MODERATE
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) remains healthy (>={SOH_HEALTHY_MIN:.0f}%)."
        )
        reasoning.append(
            f"Predicted RUL ({raw_rul:.1f} cycles) indicates battery has entered the mid-life regime ({RUL_MID_LIFE_MIN:.0f}-{RUL_EARLY_LIFE_MIN:.0f} cycles)."
        )
        reasoning.append(
            "Continued primary operation is recommended under regular diagnostic surveillance."
        )

    # CASE 2b: SOH >= 90% AND RUL < 300 cycles (Anomalous / Atypical premature cycle limit)
    elif raw_soh >= SOH_HEALTHY_MIN and raw_rul < RUL_MID_LIFE_MIN:
        category = DECISION_SECOND_LIFE_CANDIDATE
        recommended_app = APP_LIGHT_DUTY_STORAGE
        strength = STRENGTH_REVIEW_REQUIRED
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) is high (>={SOH_HEALTHY_MIN:.0f}%), but predicted RUL ({raw_rul:.1f} cycles) is low (<{RUL_MID_LIFE_MIN:.0f} cycles)."
        )
        reasoning.append(
            "Discrepancy suggests accelerated resistance growth or atypical cycle degradation."
        )
        reasoning.append(
            "Technical review required; cell is candidate for light-duty stationary energy storage."
        )

    # CASE 3: 80% <= SOH < 90% AND RUL >= 300 cycles
    elif SOH_DEGRADED_MIN <= raw_soh < SOH_HEALTHY_MIN and raw_rul >= RUL_MID_LIFE_MIN:
        category = DECISION_SECOND_LIFE_CANDIDATE
        recommended_app = APP_STATIONARY_STORAGE
        strength = STRENGTH_STRONG if raw_rul >= 500.0 else STRENGTH_MODERATE
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) indicates first-life capacity loss below primary automotive threshold ({SOH_DEGRADED_MIN:.0f}%-{SOH_HEALTHY_MIN:.0f}%)."
        )
        reasoning.append(
            f"Predicted RUL ({raw_rul:.1f} cycles) remains well above the second-life operational threshold (>={RUL_MID_LIFE_MIN:.0f} cycles)."
        )
        reasoning.append(
            "Cell is an optimal candidate for stationary energy storage (e.g. grid buffering or solar storage)."
        )

    # CASE 4: 80% <= SOH < 90% AND RUL < 300 cycles
    elif SOH_DEGRADED_MIN <= raw_soh < SOH_HEALTHY_MIN and raw_rul < RUL_MID_LIFE_MIN:
        category = DECISION_SECOND_LIFE_CANDIDATE
        recommended_app = APP_LIGHT_DUTY_STORAGE
        strength = STRENGTH_REVIEW_REQUIRED
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) retains second-life potential ({SOH_DEGRADED_MIN:.0f}%-{SOH_HEALTHY_MIN:.0f}%)."
        )
        reasoning.append(
            f"Predicted RUL ({raw_rul:.1f} cycles) is limited (<{RUL_MID_LIFE_MIN:.0f} cycles)."
        )
        reasoning.append(
            "Cell is suitable only for light-duty low-cycle stationary backup applications; technical review required."
        )

    # CASE 5: SOH < 80% AND RUL >= 300 cycles
    elif raw_soh < SOH_DEGRADED_MIN and raw_rul >= RUL_MID_LIFE_MIN:
        category = DECISION_SECOND_LIFE_CANDIDATE
        recommended_app = APP_STATIONARY_STORAGE
        strength = STRENGTH_REVIEW_REQUIRED
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) has fallen below the primary retirement threshold (<{SOH_DEGRADED_MIN:.0f}%)."
        )
        reasoning.append(
            f"Predicted RUL ({raw_rul:.1f} cycles) indicates residual cycle endurance remains under gentle cycling."
        )
        reasoning.append(
            "Critical SOH regime — mandatory diagnostic and safety inspection required before secondary stationary repurposing."
        )

    # CASE 6: SOH < 80% AND RUL < 300 cycles (including negative raw RUL)
    else:
        category = DECISION_MATERIAL_RECYCLING
        recommended_app = APP_MATERIAL_RECOVERY
        strength = STRENGTH_STRONG
        reasoning.append(
            f"Predicted SOH ({raw_soh:.2f}%) is in the critical knee degradation regime (<{SOH_DEGRADED_MIN:.0f}%)."
        )
        if raw_rul < 0.0:
            reasoning.append(
                f"Authoritative raw RUL ({raw_rul:.2f} cycles) is negative, indicating cell has exceeded nominal end-of-life (display bounded to {display_rul:.1f} cycles)."
            )
        else:
            reasoning.append(
                f"Predicted RUL ({raw_rul:.1f} cycles) is below retirement threshold (<{RUL_MID_LIFE_MIN:.0f} cycles)."
            )
        reasoning.append(
            "Cell is economically and technically exhausted; direct material recycling for mineral recovery is recommended."
        )

    return {
        "decision": {
            "category": category,
            "recommended_application": recommended_app,
            "decision_strength": strength
        },
        "regimes": {
            "soh": soh_regime,
            "rul": rul_regime
        },
        "reasoning": reasoning,
        "rules": THRESHOLD_DEFINITIONS
    }
