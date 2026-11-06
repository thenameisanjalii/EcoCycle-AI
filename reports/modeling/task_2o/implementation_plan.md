# EcoCycle AI — Task 2O Implementation Plan: Second-Life Decision Engine

**Date:** September 2026  
**Pipeline Stage:** Task 2O — Second-Life Decision Engine  
**Status:** Completed & Fully Certified  

---

## 1. Executive Summary & Context

Task 2O establishes a deterministic, rule-based Second-Life Decision Engine directly atop the certified Task 2M.4/2N production inference infrastructure. The engine translates certified machine-learning predictions—State of Health (SOH) from `soh_xgboost_32f` and Remaining Useful Life (RUL) from `rul_catboost_32f`—into actionable, transparent battery repurposing directives (`PRIMARY_OPERATION`, `SECOND_LIFE_CANDIDATE`, `MATERIAL_RECYCLING`).

### Strict Invariants & Non-Negotiable Boundaries
1. **Zero Retraining or Model Modification:** The certified machine learning estimators (`soh_xgboost_32f` and `rul_catboost_32f`) remain completely untouched. No weights, trees, or hyperparameters are modified.
2. **Immutable Data Partitioning:** The raw training, validation, and quarantined test sets are never accessed for threshold tuning or rule fitting.
3. **Cryptographic Integrity:** Artifact hashes for `master_dataset.csv` and both joblib model binaries are preserved byte-for-byte.
4. **Authoritative Raw Output Preservation:** Raw, unclipped regression predictions remain authoritative for auditability; presentation-layer clipping (`[0.0, 100.0]` for SOH, `max(0.0, rul)` for RUL) is isolated to display fields.
5. **Deterministic Logic:** All classifications and recommendations derive strictly from transparent Python rule evaluations—no heuristic randomness, probabilistic hallucinations, or ungrounded assertions.
6. **Qualitative Decision Strength:** Expressed strictly as qualitative confidence in rule clarity (`STRONG`, `MODERATE`, `REVIEW_REQUIRED`), explicitly disclaiming any representation as an ML-calibrated probability.
7. **Explicit Disclaimer:** All API and demo responses incorporate a mandatory notice declaring the engine a demonstration/decision-support system rather than an industrial battery safety certification.

---

## 2. Technical Architecture & Component Design

```
+-----------------------------------------------------------------------------------+
|                            FastAPI Ingress Layer                                  |
|     POST /predict (Task 2N)   |   POST /predict/batch   |   POST /decision/assess |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                        Input Validation & Anti-Leakage                            |
|             (src/models/input_validation.py — 32 Causal Features)                 |
|             - Rejects: QDischarge, max_cycle, final_cycle, SOH, RUL               |
|             - Enforces physical bounds (cycle >= 1, QCharge >= 0, etc.)           |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                       Certified Machine Learning Estimators                       |
|           - SOH: soh_xgboost_32f (RMSE: 0.7084%, R²: 0.9733)                      |
|           - RUL: rul_catboost_32f (RMSE: 186.36 cyc, R²: 0.8228)                  |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                     Dual Prediction Representation Layer                          |
|             - Raw Authoritative (Unclipped, e.g., raw_rul = -15.12)               |
|             - Display Presentation (Bounded, e.g., display_rul = 0.0)             |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                      Deterministic Second-Life Decision Engine                    |
|                        (src/decision/rules.py & engine.py)                        |
|                                                                                   |
|    SOH Regimes:                     RUL Regimes:                                  |
|      >= 90%: Healthy Normal Aging     >= 800: Early Life                          |
|      80-90%: Degraded Second Life     300-800: Mid Life                           |
|      < 80%:  Critical Knee EOL        < 300:  Near End of Life                    |
|                                                                                   |
|                         9-Cell Evaluation Matrix                                  |
|    - Primary Operation (Continued Primary Operation)                              |
|    - Second-Life Candidate (Stationary Storage / Light Duty)                      |
|    - Material Recycling (Direct Material Recovery)                                |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                           Unified Structured Output                               |
|        - Metadata Preservation (battery_id, row_id)                               |
|        - Dual Predictions (raw, display, units)                                   |
|        - Categorized Regimes & Step-by-Step Deterministic Reasoning               |
|        - Rule Thresholds & Model Provenance Metadata                              |
|        - Non-Certification Safety Disclaimer                                      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Implementation Details by Component

### A. Constants & Threshold Configuration (`src/decision/constants.py`)
- SOH thresholds:
  - `SOH_HEALTHY_MIN = 90.0`
  - `SOH_DEGRADED_MIN = 80.0`
- RUL thresholds:
  - `RUL_EARLY_LIFE_MIN = 800.0`
  - `RUL_MID_LIFE_MIN = 300.0`
- Lifecycle action categories:
  - `PRIMARY_OPERATION`
  - `SECOND_LIFE_CANDIDATE`
  - `MATERIAL_RECYCLING`
- Application mappings:
  - `CONTINUED_PRIMARY_OPERATION`
  - `STATIONARY_ENERGY_STORAGE`
  - `LIGHT_DUTY_STATIONARY_STORAGE`
  - `DIRECT_MATERIAL_RECOVERY`
- Qualitative strength levels: `STRONG`, `MODERATE`, `REVIEW_REQUIRED`.
- Mandatory disclaimer constant: `"Second-life suitability is a project-defined decision-support assessment based on empirical demonstration rules and is not a battery safety certification."`

### B. Pydantic Schemas (`src/decision/schemas.py`)
- Standardized data models using Pydantic v2:
  - `DecisionDetail`: `category`, `recommended_application`, `decision_strength`
  - `ValuePredictionDetail`: `raw`, `display`, `units`
  - `PredictionsSummary`: `soh`, `rul`
  - `RegimeDetail`: `soh`, `rul`
  - `RuleThresholdsDetail`: `soh_thresholds`, `rul_thresholds`
  - `ProvenanceDetail`: `pipeline_version`, `soh_model_id`, `rul_model_id`, `engine_version`, `decision_type`
  - `SecondLifeAssessmentResponse`: Complete unified API response with metadata, reasoning steps, and disclaimer.

### C. Pure Deterministic Rules (`src/decision/rules.py`)
- `get_soh_regime(soh: float) -> str`: Maps SOH into `HEALTHY_NORMAL_AGING`, `DEGRADED_SECOND_LIFE_CANDIDATE`, or `CRITICAL_KNEE_PRIMARY_RETIREMENT`.
- `get_rul_regime(rul: float) -> str`: Maps RUL (handling negative raw values via display bounding) into `EARLY_LIFE`, `MID_LIFE`, or `NEAR_END_OF_LIFE`.
- `evaluate_second_life_decision(raw_soh, raw_rul, display_soh, display_rul) -> dict`: Evaluates the exhaustive 9-combination decision matrix, producing granular step-by-step reasoning for full explainability.

### D. Engine Orchestration (`src/decision/engine.py`)
- `SecondLifeDecisionEngine`:
  - Enforces model registry provenance integration.
  - Implements `assess_from_predictions(raw_soh, raw_rul, metadata)` for direct decision scoring.
  - Implements `assess_telemetry(telemetry_record)` for end-to-end inference and decision assessment.
  - Singleton accessor `get_default_decision_engine()`.

### E. REST API Endpoint (`backend/app/api/decision_routes.py` & `main.py`)
- Exposes `POST /decision/assess`:
  - Accepts `BatteryCycleTelemetry` (32 causal features + client metadata).
  - Executes strict anti-leakage checks via `validate_inference_input` (rejecting forbidden features with HTTP 422).
  - Invokes certified model estimators via `predict_all`.
  - Evaluates decision matrix and returns `SecondLifeAssessmentResponse`.
  - Registered in `backend/app/api/main.py` and reflected in root endpoint `/`.

---

## 4. Verification & Testing Strategy

1. **Unit Tests (`tests/test_decision_engine.py` — 21 Tests):**
   - Full 9-cell matrix coverage parameterized across exact boundary coordinates.
   - Boundary tests ($\pm 0.0001$ around 90%, 80%, 800 cyc, 300 cyc).
   - Extreme value tests (0% SOH, 100% SOH, negative raw RUL, extreme cycle counts).
   - Determinism verification (10 identical runs).
   - Raw vs. display preservation tests.
2. **API Integration Tests (`tests/test_decision_api.py` — 19 Tests):**
   - Live endpoint calls using FastAPI `TestClient`.
   - Response schema conformance.
   - Metadata preservation (`battery_id`, `row_id`).
   - Anti-leakage interception (`QDischarge`, `max_cycle`, `final_cycle`, `terminal_cycle`, `total_cycles`, `SOH`, `RUL`).
   - Input validation (missing features, NaNs, Infs, out-of-bounds sensor values).
   - Disclaimer and provenance presence.
3. **Regression Suite (`tests/` — 85 Total Tests):**
   - All 45 existing Task 2M.4 and Task 2N tests passing without modification.
   - Total test count: 85 passing tests.
4. **Interactive Demonstration (`scripts/demo_decision.py`):**
   - End-to-end CLI demonstration covering Scenarios A through F.
