"""
EcoCycle AI — Second-Life Decision Engine Module
Task 2O — Second-Life Decision Engine

Public exports for the decision engine.
"""

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
    DECISION_DISCLAIMER
)
from .rules import (
    get_soh_regime,
    get_rul_regime,
    evaluate_second_life_decision
)
from .engine import (
    SecondLifeDecisionEngine,
    get_default_decision_engine
)
from .schemas import (
    DecisionDetail,
    ValuePredictionDetail,
    PredictionsSummary,
    RegimeDetail,
    RuleThresholdsDetail,
    ProvenanceDetail,
    SecondLifeAssessmentResponse
)

__all__ = [
    "SOH_HEALTHY_MIN",
    "SOH_DEGRADED_MIN",
    "RUL_EARLY_LIFE_MIN",
    "RUL_MID_LIFE_MIN",
    "SOH_REGIME_HEALTHY",
    "SOH_REGIME_DEGRADED",
    "SOH_REGIME_CRITICAL",
    "RUL_REGIME_EARLY",
    "RUL_REGIME_MID",
    "RUL_REGIME_NEAR_EOL",
    "DECISION_PRIMARY_OPERATION",
    "DECISION_SECOND_LIFE_CANDIDATE",
    "DECISION_MATERIAL_RECYCLING",
    "APP_CONTINUED_PRIMARY",
    "APP_STATIONARY_STORAGE",
    "APP_LIGHT_DUTY_STORAGE",
    "APP_MATERIAL_RECOVERY",
    "STRENGTH_STRONG",
    "STRENGTH_MODERATE",
    "STRENGTH_REVIEW_REQUIRED",
    "DECISION_DISCLAIMER",
    "get_soh_regime",
    "get_rul_regime",
    "evaluate_second_life_decision",
    "SecondLifeDecisionEngine",
    "get_default_decision_engine",
    "DecisionDetail",
    "ValuePredictionDetail",
    "PredictionsSummary",
    "RegimeDetail",
    "RuleThresholdsDetail",
    "ProvenanceDetail",
    "SecondLifeAssessmentResponse"
]
