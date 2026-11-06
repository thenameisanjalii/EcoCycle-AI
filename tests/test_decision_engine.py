"""
Unit Tests for Task 2O Second-Life Decision Engine
Tests decision matrix, regime mapping, boundary cases, determinism, and raw preservation.
"""

import pytest
from src.decision.constants import (
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
from src.decision.rules import (
    get_soh_regime,
    get_rul_regime,
    evaluate_second_life_decision
)
from src.decision.engine import get_default_decision_engine, SecondLifeDecisionEngine
from src.decision.schemas import SecondLifeAssessmentResponse


# =========================================================================
# 1. REGIME CLASSIFICATION TESTS
# =========================================================================

def test_soh_regime_classification():
    """Verify SOH values map to exact degradation regimes."""
    assert get_soh_regime(95.0) == SOH_REGIME_HEALTHY
    assert get_soh_regime(90.0) == SOH_REGIME_HEALTHY
    assert get_soh_regime(89.99) == SOH_REGIME_DEGRADED
    assert get_soh_regime(85.0) == SOH_REGIME_DEGRADED
    assert get_soh_regime(80.0) == SOH_REGIME_DEGRADED
    assert get_soh_regime(79.99) == SOH_REGIME_CRITICAL
    assert get_soh_regime(50.0) == SOH_REGIME_CRITICAL
    assert get_soh_regime(0.0) == SOH_REGIME_CRITICAL


def test_rul_regime_classification():
    """Verify RUL values map to exact operational regimes."""
    assert get_rul_regime(1200.0) == RUL_REGIME_EARLY
    assert get_rul_regime(800.0) == RUL_REGIME_EARLY
    assert get_rul_regime(799.99) == RUL_REGIME_MID
    assert get_rul_regime(500.0) == RUL_REGIME_MID
    assert get_rul_regime(300.0) == RUL_REGIME_MID
    assert get_rul_regime(299.99) == RUL_REGIME_NEAR_EOL
    assert get_rul_regime(50.0) == RUL_REGIME_NEAR_EOL
    assert get_rul_regime(0.0) == RUL_REGIME_NEAR_EOL
    assert get_rul_regime(-30.48) == RUL_REGIME_NEAR_EOL


# =========================================================================
# 2. ALL 9 COMBINATIONS OF SOH × RUL REGIMES
# =========================================================================

@pytest.mark.parametrize(
    "raw_soh,raw_rul,disp_soh,disp_rul,expected_cat,expected_app,expected_strength,expected_soh_reg,expected_rul_reg",
    [
        # 1. Healthy (>=90) × Early (>=800)
        (95.0, 900.0, 95.0, 900.0, DECISION_PRIMARY_OPERATION, APP_CONTINUED_PRIMARY, STRENGTH_STRONG, SOH_REGIME_HEALTHY, RUL_REGIME_EARLY),
        # 2. Healthy (>=90) × Mid (300-800)
        (92.0, 550.0, 92.0, 550.0, DECISION_PRIMARY_OPERATION, APP_CONTINUED_PRIMARY, STRENGTH_MODERATE, SOH_REGIME_HEALTHY, RUL_REGIME_MID),
        # 3. Healthy (>=90) × Near EOL (<300)
        (91.0, 150.0, 91.0, 150.0, DECISION_SECOND_LIFE_CANDIDATE, APP_LIGHT_DUTY_STORAGE, STRENGTH_REVIEW_REQUIRED, SOH_REGIME_HEALTHY, RUL_REGIME_NEAR_EOL),
        # 4. Degraded (80-90) × Early (>=800)
        (85.0, 850.0, 85.0, 850.0, DECISION_SECOND_LIFE_CANDIDATE, APP_STATIONARY_STORAGE, STRENGTH_STRONG, SOH_REGIME_DEGRADED, RUL_REGIME_EARLY),
        # 5. Degraded (80-90) × Mid (300-800)
        (84.0, 600.0, 84.0, 600.0, DECISION_SECOND_LIFE_CANDIDATE, APP_STATIONARY_STORAGE, STRENGTH_STRONG, SOH_REGIME_DEGRADED, RUL_REGIME_MID),
        (84.0, 400.0, 84.0, 400.0, DECISION_SECOND_LIFE_CANDIDATE, APP_STATIONARY_STORAGE, STRENGTH_MODERATE, SOH_REGIME_DEGRADED, RUL_REGIME_MID),
        # 6. Degraded (80-90) × Near EOL (<300)
        (82.0, 200.0, 82.0, 200.0, DECISION_SECOND_LIFE_CANDIDATE, APP_LIGHT_DUTY_STORAGE, STRENGTH_REVIEW_REQUIRED, SOH_REGIME_DEGRADED, RUL_REGIME_NEAR_EOL),
        # 7. Critical (<80) × Early (>=800)
        (75.0, 850.0, 75.0, 850.0, DECISION_SECOND_LIFE_CANDIDATE, APP_STATIONARY_STORAGE, STRENGTH_REVIEW_REQUIRED, SOH_REGIME_CRITICAL, RUL_REGIME_EARLY),
        # 8. Critical (<80) × Mid (300-800)
        (76.0, 450.0, 76.0, 450.0, DECISION_SECOND_LIFE_CANDIDATE, APP_STATIONARY_STORAGE, STRENGTH_REVIEW_REQUIRED, SOH_REGIME_CRITICAL, RUL_REGIME_MID),
        # 9. Critical (<80) × Near EOL (<300)
        (72.0, 120.0, 72.0, 120.0, DECISION_MATERIAL_RECYCLING, APP_MATERIAL_RECOVERY, STRENGTH_STRONG, SOH_REGIME_CRITICAL, RUL_REGIME_NEAR_EOL),
        # 9b. Critical (<80) × Negative Raw RUL (<0)
        (68.0, -30.48, 68.0, 0.0, DECISION_MATERIAL_RECYCLING, APP_MATERIAL_RECOVERY, STRENGTH_STRONG, SOH_REGIME_CRITICAL, RUL_REGIME_NEAR_EOL),
    ]
)
def test_all_decision_matrix_combinations(
    raw_soh, raw_rul, disp_soh, disp_rul,
    expected_cat, expected_app, expected_strength,
    expected_soh_reg, expected_rul_reg
):
    """Verify all 9 matrix combinations evaluate to the exact expected decision, application, and regimes."""
    res = evaluate_second_life_decision(raw_soh, raw_rul, disp_soh, disp_rul)
    assert res["decision"]["category"] == expected_cat
    assert res["decision"]["recommended_application"] == expected_app
    assert res["decision"]["decision_strength"] == expected_strength
    assert res["regimes"]["soh"] == expected_soh_reg
    assert res["regimes"]["rul"] == expected_rul_reg
    assert isinstance(res["reasoning"], list)
    assert len(res["reasoning"]) >= 2


# =========================================================================
# 3. CRITICAL BOUNDARY TESTS (TOLERANCE ±0.0001)
# =========================================================================

def test_soh_boundary_90():
    """Verify exact boundary transition at SOH = 90.0%."""
    # 89.9999 -> DEGRADED
    res_below = evaluate_second_life_decision(89.9999, 900.0, 89.9999, 900.0)
    assert res_below["regimes"]["soh"] == SOH_REGIME_DEGRADED
    assert res_below["decision"]["category"] == DECISION_SECOND_LIFE_CANDIDATE

    # 90.0 -> HEALTHY
    res_exact = evaluate_second_life_decision(90.0, 900.0, 90.0, 900.0)
    assert res_exact["regimes"]["soh"] == SOH_REGIME_HEALTHY
    assert res_exact["decision"]["category"] == DECISION_PRIMARY_OPERATION

    # 90.0001 -> HEALTHY
    res_above = evaluate_second_life_decision(90.0001, 900.0, 90.0001, 900.0)
    assert res_above["regimes"]["soh"] == SOH_REGIME_HEALTHY
    assert res_above["decision"]["category"] == DECISION_PRIMARY_OPERATION


def test_soh_boundary_80():
    """Verify exact boundary transition at SOH = 80.0%."""
    # 79.9999 -> CRITICAL
    res_below = evaluate_second_life_decision(79.9999, 200.0, 79.9999, 200.0)
    assert res_below["regimes"]["soh"] == SOH_REGIME_CRITICAL
    assert res_below["decision"]["category"] == DECISION_MATERIAL_RECYCLING

    # 80.0 -> DEGRADED
    res_exact = evaluate_second_life_decision(80.0, 200.0, 80.0, 200.0)
    assert res_exact["regimes"]["soh"] == SOH_REGIME_DEGRADED
    assert res_exact["decision"]["category"] == DECISION_SECOND_LIFE_CANDIDATE

    # 80.0001 -> DEGRADED
    res_above = evaluate_second_life_decision(80.0001, 200.0, 80.0001, 200.0)
    assert res_above["regimes"]["soh"] == SOH_REGIME_DEGRADED
    assert res_above["decision"]["category"] == DECISION_SECOND_LIFE_CANDIDATE


def test_rul_boundary_800():
    """Verify exact boundary transition at RUL = 800.0 cycles."""
    # 799.9999 -> MID_LIFE
    res_below = evaluate_second_life_decision(95.0, 799.9999, 95.0, 799.9999)
    assert res_below["regimes"]["rul"] == RUL_REGIME_MID
    assert res_below["decision"]["decision_strength"] == STRENGTH_MODERATE

    # 800.0 -> EARLY_LIFE
    res_exact = evaluate_second_life_decision(95.0, 800.0, 95.0, 800.0)
    assert res_exact["regimes"]["rul"] == RUL_REGIME_EARLY
    assert res_exact["decision"]["decision_strength"] == STRENGTH_STRONG

    # 800.0001 -> EARLY_LIFE
    res_above = evaluate_second_life_decision(95.0, 800.0001, 95.0, 800.0001)
    assert res_above["regimes"]["rul"] == RUL_REGIME_EARLY
    assert res_above["decision"]["decision_strength"] == STRENGTH_STRONG


def test_rul_boundary_300():
    """Verify exact boundary transition at RUL = 300.0 cycles."""
    # 299.9999 -> NEAR_END_OF_LIFE
    res_below = evaluate_second_life_decision(75.0, 299.9999, 75.0, 299.9999)
    assert res_below["regimes"]["rul"] == RUL_REGIME_NEAR_EOL
    assert res_below["decision"]["category"] == DECISION_MATERIAL_RECYCLING

    # 300.0 -> MID_LIFE
    res_exact = evaluate_second_life_decision(75.0, 300.0, 75.0, 300.0)
    assert res_exact["regimes"]["rul"] == RUL_REGIME_MID
    assert res_exact["decision"]["category"] == DECISION_SECOND_LIFE_CANDIDATE
    assert res_exact["decision"]["decision_strength"] == STRENGTH_REVIEW_REQUIRED

    # 300.0001 -> MID_LIFE
    res_above = evaluate_second_life_decision(75.0, 300.0001, 75.0, 300.0001)
    assert res_above["regimes"]["rul"] == RUL_REGIME_MID
    assert res_above["decision"]["category"] == DECISION_SECOND_LIFE_CANDIDATE


# =========================================================================
# 4. EXTREME AND NEGATIVE VALUE TESTS
# =========================================================================

def test_extreme_values():
    """Verify handling of extreme sensor values: 0%, 100%, negative RUL."""
    # SOH = 100%, RUL = 1500 -> Primary
    res_top = evaluate_second_life_decision(100.0, 1500.0, 100.0, 1500.0)
    assert res_top["decision"]["category"] == DECISION_PRIMARY_OPERATION

    # SOH = 0%, RUL = 0 -> Recycling
    res_zero = evaluate_second_life_decision(0.0, 0.0, 0.0, 0.0)
    assert res_zero["decision"]["category"] == DECISION_MATERIAL_RECYCLING
    assert res_zero["regimes"]["soh"] == SOH_REGIME_CRITICAL
    assert res_zero["regimes"]["rul"] == RUL_REGIME_NEAR_EOL

    # Negative raw RUL
    res_neg = evaluate_second_life_decision(76.5, -45.2, 76.5, 0.0)
    assert res_neg["decision"]["category"] == DECISION_MATERIAL_RECYCLING
    assert any("negative" in r.lower() for r in res_neg["reasoning"])


# =========================================================================
# 5. ENGINE INTEGRATION, DETERMINISM & SCHEMA VALIDATION
# =========================================================================

def test_decision_engine_determinism():
    """Verify 10 repeated evaluations yield exact identical structured outputs."""
    engine = get_default_decision_engine()
    results = [engine.assess_from_predictions(84.5, 620.0) for _ in range(10)]

    for i in range(1, 10):
        assert results[i] == results[0]


def test_engine_schema_conformance():
    """Verify that engine output strictly satisfies SecondLifeAssessmentResponse schema."""
    engine = get_default_decision_engine()
    out = engine.assess_from_predictions(85.0, 650.0, metadata={"battery_id": 99, "row_id": "test_row"})

    # Validates with Pydantic
    resp = SecondLifeAssessmentResponse(**out)
    assert resp.status == "success"
    assert resp.metadata["battery_id"] == 99
    assert resp.predictions.soh.raw == 85.0
    assert resp.predictions.rul.raw == 650.0
    assert resp.decision.category == DECISION_SECOND_LIFE_CANDIDATE
    assert resp.provenance.soh_model_id == "soh_xgboost_32f"
    assert resp.provenance.rul_model_id == "rul_catboost_32f"
    assert resp.disclaimer == DECISION_DISCLAIMER


def test_raw_prediction_unclipped_preservation():
    """Verify engine preserves unclipped negative raw RUL while computing display bound."""
    engine = get_default_decision_engine()
    raw_s = 77.2
    raw_r = -30.4818

    out = engine.assess_from_predictions(raw_s, raw_r)
    # Raw predictions must remain strictly identical to input
    assert out["predictions"]["soh"]["raw"] == raw_s
    assert out["predictions"]["rul"]["raw"] == raw_r

    # Presentation display values must be bounded
    assert out["predictions"]["rul"]["display"] == 0.0
    assert out["predictions"]["soh"]["display"] == raw_s
