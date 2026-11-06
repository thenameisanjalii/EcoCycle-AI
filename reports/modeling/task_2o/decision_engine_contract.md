# EcoCycle AI — Second-Life Decision Engine Contract (Task 2O)

**Pipeline Stage:** Task 2O — Second-Life Decision Engine  
**Version:** 2O.1 (task_2o_v1)  
**Status:** Certified & Production-Locked  

---

## 1. Scope & Objective

The **Second-Life Decision Engine** is a deterministic, rule-based interpretation system that translates certified machine learning predictions for State of Health (SOH) and Remaining Useful Life (RUL) into actionable, auditable lifecycle directives.

> [!IMPORTANT]
> **Methodological Disclaimer:**
> The decision rules and thresholds defined herein are empirical, project-level demonstration heuristics derived from lithium-ion degradation dynamics. This system provides automated decision support and does **NOT** constitute an official industrial battery safety certification or regulatory compliance guarantee.

---

## 2. Input Specification & Anti-Leakage Constraints

The decision engine accepts either raw cycle telemetry (via `assess_telemetry` / `POST /decision/assess`) or pre-inferred regression predictions (via `assess_from_predictions`).

### Required 32 Causal Features (for Telemetry Input)
| Feature Group | Features |
| :--- | :--- |
| **Physical Measurements (6)** | `IR`, `QCharge`, `Tavg`, `Tmax`, `Tmin`, `chargetime` |
| **Temporal Dynamics (1)** | `cycle` (must be $\ge 1$) |
| **Sensor Fault Flags (2)** | `IR_is_zero`, `temp_sensor_fault` |
| **First-Order Lags (4)** | `IR_lag1`, `IR_delta`, `QCharge_lag1`, `QCharge_delta`, `Tavg_lag1`, `Tavg_delta`, `chargetime_lag1`, `chargetime_delta` |
| **Second-Order Accel (4)** | `IR_accel`, `QCharge_accel`, `Tavg_accel`, `chargetime_accel` |
| **Physical Ratios & Rolling (7)** | `thermal_dissipation_rate`, `charge_efficiency_proxy`, `resistance_growth_ratio`, `IR_roll_mean_5`, `IR_roll_std_5`, `QCharge_roll_mean_5`, `QCharge_roll_std_5`, `Tavg_roll_mean_5`, `Tavg_roll_std_5` |
| **Cumulative Slopes (2)** | `cum_capacity_fade_rate`, `cum_resistance_growth_rate` |

### Preserved Metadata (Excluded from Features)
- `battery_id` (Integer or String): Cell/pack identifier.
- `row_id` (Integer or String): Telemetry cycle logging key.

### Strictly Forbidden Features (Anti-Leakage Rejection: HTTP 422)
Any request containing the following keys is rejected immediately prior to feature transformation or ML inference:
- `QDischarge` (direct target proxy)
- `max_cycle`, `final_cycle`, `terminal_cycle`, `total_cycles` (future lifespan lookahead)
- `SOH`, `RUL` (cross-target label leakage)

---

## 3. Operational Regimes & Empirical Thresholds

### SOH Degradation Regimes
| Regime Key | SOH Retention ($\%$) | Technical Interpretation |
| :--- | :--- | :--- |
| `HEALTHY_NORMAL_AGING` | $\text{SOH} \ge 90.0\%$ | Cell demonstrates nominal capacity retention with minimal solid electrolyte interphase (SEI) growth. Retains full capability for demanding primary mobility/industrial duty. |
| `DEGRADED_SECOND_LIFE_CANDIDATE` | $80.0\% \le \text{SOH} < 90.0\%$ | Cell has degraded beyond primary automotive standard thresholds ($80\%\text{--}90\%$) but retains significant reversible capacity. Prime candidate for secondary energy storage. |
| `CRITICAL_KNEE_PRIMARY_RETIREMENT` | $\text{SOH} < 80.0\%$ | Cell has reached or passed the non-linear degradation "knee." Acceleration of capacity loss and internal resistance growth precludes demanding primary use. |

### RUL Operational Regimes
| Regime Key | Residual RUL (Cycles) | Technical Interpretation |
| :--- | :--- | :--- |
| `EARLY_LIFE` | $\text{RUL} \ge 800.0$ cycles | Substantial remaining cycle endurance under nominal charge/discharge protocols. |
| `MID_LIFE` | $300.0 \le \text{RUL} < 800.0$ cycles | Moderate residual cycle life; operational cycles should be planned with regular monitoring. |
| `NEAR_END_OF_LIFE` | $\text{RUL} < 300.0$ cycles | Cell is nearing or has surpassed its designated operating lifecycle boundary. |

---

## 4. Exhaustive 9-Cell Decision Matrix

The decision engine deterministically evaluates the intersection of the 3 SOH regimes and 3 RUL regimes across exactly 9 states:

| SOH Regime | RUL Regime | Action Category | Recommended Application | Decision Strength | Rationale & Operational Directive |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Healthy** ($\ge 90\%$) | **Early** ($\ge 800$) | `PRIMARY_OPERATION` | `CONTINUED_PRIMARY_OPERATION` | `STRONG` | Both capacity and cycle life are robust. Unrestricted primary deployment. |
| **Healthy** ($\ge 90\%$) | **Mid** ($300\text{--}800$) | `PRIMARY_OPERATION` | `CONTINUED_PRIMARY_OPERATION` | `MODERATE` | Cell remains healthy, but cycle count is progressing. Primary service continued with scheduled diagnostics. |
| **Healthy** ($\ge 90\%$) | **Near EOL** ($< 300$) | `SECOND_LIFE_CANDIDATE` | `LIGHT_DUTY_STATIONARY_STORAGE` | `REVIEW_REQUIRED` | High capacity retention paired with low cycle endurance suggests atypical degradation (e.g., calendar aging or impedance rise). Suitable for light-duty stationary backup; engineering review required. |
| **Degraded** ($80\%\text{--}90\%$) | **Early** ($\ge 800$) | `SECOND_LIFE_CANDIDATE` | `STATIONARY_ENERGY_STORAGE` | `STRONG` | Ideal repurposing profile: retired from primary service but possesses long residual cycle endurance for grid or commercial stationary storage. |
| **Degraded** ($80\%\text{--}90\%$) | **Mid** ($300\text{--}800$) | `SECOND_LIFE_CANDIDATE` | `STATIONARY_ENERGY_STORAGE` | `STRONG` ($\ge 500$ cyc) / `MODERATE` ($< 500$ cyc) | Viable second-life candidate for stationary peak-shaving or solar storage under moderate cycling profiles. |
| **Degraded** ($80\%\text{--}90\%$) | **Near EOL** ($< 300$) | `SECOND_LIFE_CANDIDATE` | `LIGHT_DUTY_STATIONARY_STORAGE` | `REVIEW_REQUIRED` | Marginal residual cycle life. Restricted to low-cycling stationary reserve / emergency backup; safety review required. |
| **Critical** ($< 80\%$) | **Early** ($\ge 800$) | `SECOND_LIFE_CANDIDATE` | `STATIONARY_ENERGY_STORAGE` | `REVIEW_REQUIRED` | Atypical knee profile: capacity is sub-80% but model predicts high cycle endurance. Pre-repurposing bench screening mandatory to verify cell stability. |
| **Critical** ($< 80\%$) | **Mid** ($300\text{--}800$) | `SECOND_LIFE_CANDIDATE` | `STATIONARY_ENERGY_STORAGE` | `REVIEW_REQUIRED` | Near-knee cell with moderate cycles. Mandatory electrochemical impedance spectroscopy (EIS) and thermal testing required prior to any second-life repurposing. |
| **Critical** ($< 80\%$) | **Near EOL** ($< 300$) | `MATERIAL_RECYCLING` | `DIRECT_MATERIAL_RECOVERY` | `STRONG` | Both capacity and cycle endurance are exhausted. Direct routing to hydrometallurgical/pyrometallurgical material recovery for lithium, cobalt, and nickel extraction. |

---

## 5. Raw vs Presentation Prediction Contract

To preserve scientific auditability and eliminate silent data distortion:
1. **Raw Unclipped Predictions:** Machine learning outputs (`soh_xgboost_32f` and `rul_catboost_32f`) are recorded exactly as computed by the regressors without artificial bounding (e.g., `raw_rul = -15.12 cycles`, `raw_soh = 101.2%`).
2. **Display Bounded Values:** Dedicated user-facing presentation fields enforce physical plausibility for dashboards and client interfaces:
   $$\text{display\_soh} = \max(0.0, \min(100.0, \text{raw\_soh}))$$
   $$\text{display\_rul} = \max(0.0, \text{raw\_rul})$$
3. **Decision Logic Evaluation:**
   - SOH regimes are classified using `display_soh` (or unclipped raw, which are identical within the valid operational range).
   - RUL regimes recognize non-positive raw values ($\text{raw\_rul} \le 0$) as unambiguous `NEAR_END_OF_LIFE` states, ensuring cells operating past their nominal cycle limit are promptly routed to `MATERIAL_RECYCLING`.

---

## 6. Qualitative Decision Strength Contract

Decision strength reflects the **clarity and unambiguity of the deterministic business rule application**, not an ML-derived Bayesian probability:
- **`STRONG`**: Both SOH and RUL metrics fall comfortably within unambiguous operational zones (e.g., SOH $> 90\%$ & RUL $> 800$, or SOH $< 80\%$ & RUL $< 300$).
- **`MODERATE`**: Metrics sit in intermediate regimes where standard operational surveillance is recommended.
- **`REVIEW_REQUIRED`**: Represents edge cases, discordant metrics (e.g., high SOH with very low RUL, or low SOH with high RUL), or cells approaching critical physical inflection points where automated repurposing should not proceed without human engineering review.

---

## 7. API Contract: `POST /decision/assess`

### Request Body Schema (`BatteryCycleTelemetry`)
```json
{
  "cycle": 120.0,
  "IR": 0.0085,
  "QCharge": 1.065,
  "Tavg": 30.2,
  "Tmax": 32.5,
  "Tmin": 28.0,
  "chargetime": 40.5,
  "IR_is_zero": 0.0,
  "temp_sensor_fault": 0.0,
  "IR_lag1": 0.0084,
  "IR_delta": 0.0001,
  "QCharge_lag1": 1.066,
  "QCharge_delta": -0.001,
  "Tavg_lag1": 30.1,
  "Tavg_delta": 0.1,
  "chargetime_lag1": 40.6,
  "chargetime_delta": -0.1,
  "IR_accel": 0.00001,
  "QCharge_accel": -0.00002,
  "Tavg_accel": 0.01,
  "chargetime_accel": -0.01,
  "thermal_dissipation_rate": 0.1111,
  "charge_efficiency_proxy": 0.0263,
  "resistance_growth_ratio": 1.0119,
  "IR_roll_mean_5": 0.00845,
  "IR_roll_std_5": 0.00005,
  "QCharge_roll_mean_5": 1.066,
  "QCharge_roll_std_5": 0.0008,
  "Tavg_roll_mean_5": 30.12,
  "Tavg_roll_std_5": 0.15,
  "cum_capacity_fade_rate": 0.00025,
  "cum_resistance_growth_rate": 0.00004,
  "battery_id": 42,
  "row_id": "cell_42_cycle_120"
}
```

### Successful Response Schema (`SecondLifeAssessmentResponse`, HTTP 200)
```json
{
  "status": "success",
  "metadata": {
    "battery_id": 42,
    "row_id": "cell_42_cycle_120"
  },
  "decision": {
    "category": "PRIMARY_OPERATION",
    "recommended_application": "CONTINUED_PRIMARY_OPERATION",
    "decision_strength": "MODERATE"
  },
  "predictions": {
    "soh": {
      "raw": 97.2319,
      "display": 97.23,
      "units": "%"
    },
    "rul": {
      "raw": 528.50,
      "display": 528.50,
      "units": "cycles"
    }
  },
  "regimes": {
    "soh": "HEALTHY_NORMAL_AGING",
    "rul": "MID_LIFE"
  },
  "reasoning": [
    "Predicted SOH (97.23%) remains healthy (>=90%).",
    "Predicted RUL (528.5 cycles) indicates battery has entered the mid-life regime (300-800 cycles).",
    "Continued primary operation is recommended under regular diagnostic surveillance."
  ],
  "rules": {
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
  },
  "provenance": {
    "pipeline_version": "1.0.0",
    "soh_model_id": "soh_xgboost_32f",
    "soh_framework": "XGBoost 3.2.0",
    "rul_model_id": "rul_catboost_32f",
    "rul_framework": "CatBoost 1.2.10",
    "feature_set": "32_causal_features",
    "dataset_sha256": "0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88",
    "decision_engine": "task_2o_v1",
    "decision_type": "project-defined deterministic business rules"
  },
  "disclaimer": "Second-life suitability is a project-defined decision-support assessment based on empirical demonstration rules and is not a battery safety certification."
}
```

### HTTP Error Status Codes
- `HTTP 400 Bad Request`: Input validation error (missing features, NaNs/Infs, physical bounds violation).
- `HTTP 422 Unprocessable Entity`: Data leakage error (presence of `QDischarge`, `max_cycle`, `final_cycle`, `terminal_cycle`, `total_cycles`, `SOH`, or `RUL`).
- `HTTP 500 Internal Server Error`: Internal system or model registry failure.
