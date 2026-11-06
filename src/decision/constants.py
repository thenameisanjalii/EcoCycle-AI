"""
EcoCycle AI — Second-Life Decision Engine Constants
Task 2O — Second-Life Decision Engine

Contains explicit thresholds, operational regimes, decision categories,
recommended applications, and qualitative decision strength ratings.
IMPORTANT: Thresholds are project-defined demonstration/business rules derived
from the project's degradation interpretation framework, NOT universal industrial standards.
"""

# SOH Regime Thresholds (% Capacity Retention)
SOH_HEALTHY_MIN = 90.0
SOH_DEGRADED_MIN = 80.0

# RUL Regime Thresholds (Operating Cycles)
RUL_EARLY_LIFE_MIN = 800.0
RUL_MID_LIFE_MIN = 300.0

# SOH Regimes
SOH_REGIME_HEALTHY = "HEALTHY_NORMAL_AGING"
SOH_REGIME_DEGRADED = "DEGRADED_SECOND_LIFE_CANDIDATE"
SOH_REGIME_CRITICAL = "CRITICAL_KNEE_PRIMARY_RETIREMENT"

# RUL Regimes
RUL_REGIME_EARLY = "EARLY_LIFE"
RUL_REGIME_MID = "MID_LIFE"
RUL_REGIME_NEAR_EOL = "NEAR_END_OF_LIFE"

# Second-Life Decision Categories
DECISION_PRIMARY_OPERATION = "PRIMARY_OPERATION"
DECISION_SECOND_LIFE_CANDIDATE = "SECOND_LIFE_CANDIDATE"
DECISION_MATERIAL_RECYCLING = "MATERIAL_RECYCLING"

# Recommended Applications
APP_CONTINUED_PRIMARY = "CONTINUED_PRIMARY_OPERATION"
APP_STATIONARY_STORAGE = "STATIONARY_ENERGY_STORAGE"
APP_LIGHT_DUTY_STORAGE = "LIGHT_DUTY_STATIONARY_STORAGE"
APP_MATERIAL_RECOVERY = "DIRECT_MATERIAL_RECOVERY"

# Qualitative Decision Strength (Rule clarity, NOT probabilistic confidence)
STRENGTH_STRONG = "STRONG"
STRENGTH_MODERATE = "MODERATE"
STRENGTH_REVIEW_REQUIRED = "REVIEW_REQUIRED"

# Standard Methodological Disclaimer
DECISION_DISCLAIMER = (
    "Second-life suitability is a project-defined decision-support assessment based on "
    "empirical demonstration rules and is not a battery safety certification."
)

# Rule Threshold Documentation Metadata
THRESHOLD_DEFINITIONS = {
    "soh_thresholds": {
        "healthy_normal_aging": ">=90.0%",
        "degraded_second_life": "80.0% - 90.0%",
        "critical_knee_retirement": "<80.0%"
    },
    "rul_thresholds": {
        "early_life": ">=800.0 cycles",
        "mid_life": "300.0 - 800.0 cycles",
        "near_end_of_life": "<300.0 cycles"
    }
}
