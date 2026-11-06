# EcoCycle AI — Production Inference API Contract Specification

**Document ID:** ECOCYCLE-SPEC-TASK-2N-API-CONTRACT-001  
**Service Name:** EcoCycle AI Battery Health Prediction & Lifecycle API  
**API Version:** `1.0.0`  
**Base URL:** `http://localhost:8000`  
**Date:** 2026-09-07  

---

## 1. Overview & Architectural Principles

The EcoCycle AI REST API provides automated degradation inference for lithium-ion battery cells. It predicts both:
1. **State of Health (SOH, %):** Capacity retention relative to nominal initial capacity.
2. **Remaining Useful Life (RUL, operating cycles):** Number of operational cycles remaining until end-of-first-life.

### Core Invariants
- **Cryptographic Model Verification:** Model binaries are audited on disk against expected SHA-256 digests before loading.
- **Strict Anti-Leakage Guards:** Columns that leak future lifespan (`max_cycle`, `final_cycle`) or ground-truth targets (`QDischarge`, cross-target labels) are intercepted and rejected with `HTTP 422`.
- **Dual Output Contract:** Authoritative raw predictions (`raw`) are preserved unclipped; display-safe bounded values (`display`) are delivered in a separate schema field.
- **Deterministic Interpretation:** Operational regime classifications are provided as presentation business rules based on verified Task 2L.3 benchmarks.

---

## 2. API Endpoints

### 2.1 Service Health Check

- **URL:** `/health`
- **Method:** `GET`
- **Description:** Returns service operational status and model availability.
- **Request Parameters:** None
- **Response Codes:**
  - `200 OK`: Service operational and models loaded.

#### Response Example
```json
{
  "status": "healthy",
  "service": "EcoCycle AI Battery Health API",
  "pipeline_version": "1.0.0",
  "models_available": {
    "soh": true,
    "rul": true
  }
}
```

---

### 2.2 Model Registry & Provenance Information

- **URL:** `/model-info`
- **Method:** `GET`
- **Description:** Returns certified metadata, training architectures, hyperparameter configurations, dataset SHA-256 hash, and locked benchmark validation/test metrics.
- **Request Parameters:** None
- **Response Codes:**
  - `200 OK`: Metadata successfully retrieved.

#### Response Example
```json
{
  "project": "EcoCycle AI",
  "pipeline_stage": "Task 2M.4 — Final Model Packaging & Inference Pipeline",
  "dataset_sha256": "0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88",
  "models": {
    "soh": {
      "model_id": "soh_xgboost_32f",
      "framework": "xgboost",
      "framework_version": "3.2.0",
      "target": "SOH",
      "target_units": "%",
      "feature_count": 32,
      "validation_rmse": 0.5654,
      "test_rmse": 0.7084,
      "test_r2": 0.9733
    },
    "rul": {
      "model_id": "rul_catboost_32f",
      "framework": "catboost",
      "framework_version": "1.2.10",
      "target": "RUL",
      "target_units": "cycles",
      "feature_count": 32,
      "validation_rmse": 233.06,
      "test_rmse": 186.36,
      "test_r2": 0.8228
    }
  }
}
```

---

### 2.3 Single Cycle Telemetry Inference

- **URL:** `/predict`
- **Method:** `POST`
- **Description:** Scores a single battery operating cycle using the certified 32 causal features.
- **Headers:** `Content-Type: application/json`
- **Response Codes:**
  - `200 OK`: Successful inference.
  - `400 Bad Request`: Missing features, NaN/Inf, or physical bounds violations.
  - `422 Unprocessable Entity`: Data leakage detected (e.g. `QDischarge`, `max_cycle`).

#### Request Schema (`BatteryCycleTelemetry`)
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
  "QCharge_roll_mean_5": 1.0655,
  "QCharge_roll_std_5": 0.0007,
  "Tavg_roll_mean_5": 30.15,
  "Tavg_roll_std_5": 0.12,
  "cum_capacity_fade_rate": 0.00025,
  "cum_resistance_growth_rate": 0.00004,
  "battery_id": 42,
  "row_id": "cell_cycle_120"
}
```

#### Response Example
```json
{
  "status": "success",
  "metadata": {
    "battery_id": 42,
    "row_id": "cell_cycle_120"
  },
  "predictions": {
    "soh": {
      "raw": 97.2319,
      "display": 97.23,
      "units": "%"
    },
    "rul": {
      "raw": 528.5,
      "display": 528.5,
      "units": "cycles"
    }
  },
  "interpretation": {
    "soh": {
      "category": "Healthy (Normal Aging)",
      "description": "Capacity retention is at or above 90%. Battery is in a healthy, linear aging stage.",
      "confidence_note": "High predictive precision (MAE ~0.30%). Suitable for all primary operational demands."
    },
    "rul": {
      "category": "Mid-Life (Moderate Remaining Life)",
      "description": "Estimated remaining useful operational lifespan is between 300 and 800 cycles.",
      "confidence_note": "Reliable trajectory tracking by CatBoost 32f (MAE ~116 cyc). Normal maintenance schedule applies."
    }
  },
  "models": {
    "pipeline_version": "1.0.0",
    "soh_model_id": "soh_xgboost_32f",
    "soh_framework": "xgboost 3.2.0",
    "rul_model_id": "rul_catboost_32f",
    "rul_framework": "catboost 1.2.10",
    "feature_set": "32_causal_features"
  }
}
```

---

### 2.4 Batch Telemetry Inference

- **URL:** `/predict/batch`
- **Method:** `POST`
- **Description:** Scores up to 5,000 battery telemetry records in a single request.
- **Headers:** `Content-Type: application/json`
- **Request Schema:**
  ```json
  {
    "records": [
      { "...32 features..." },
      { "...32 features..." }
    ]
  }
  ```
- **Response Codes:**
  - `200 OK`: Batch successfully processed.
  - `400 Bad Request`: Empty batch, batch size $> 5,000$, or validation error.
  - `422 Unprocessable Entity`: Target leakage detected in any record.

---

## 3. Input Validation Rules & Admissibility Matrix

| Constraint Type | Rule | Failure Behavior |
| :--- | :--- | :--- |
| **Feature Completeness** | All 32 features must be present | `HTTP 400 Bad Request` |
| **Data Types** | Castable to 64-bit float | `HTTP 400 Bad Request` |
| **Missing Values** | Zero `null`, `NaN`, or `None` allowed | `HTTP 400 Bad Request` |
| **Infinites** | Zero `inf` or `-inf` allowed | `HTTP 400 Bad Request` |
| **Target Leakage** | `QDischarge` forbidden | `HTTP 422 DataLeakageError` |
| **Lifespan Leakage** | `max_cycle`, `final_cycle` forbidden | `HTTP 422 DataLeakageError` |
| **Cross-Target Leakage** | `SOH` in RUL / `RUL` in SOH forbidden | `HTTP 422 DataLeakageError` |
| **Operating Cycle** | $cycle \ge 1.0$ | `HTTP 400 Bad Request` |
| **Charge Capacity** | $0.0 \le QCharge \le 20.0$ Ah | `HTTP 400 Bad Request` |
| **Internal Resistance** | $0.0 \le IR \le 10.0$ Ohm | `HTTP 400 Bad Request` |
| **Temperature** | $-20^\circ\text{C} \le Tavg \le 100^\circ\text{C}$ | `HTTP 400 Bad Request` |

---

## 4. Degradation Interpretation Regimes

### SOH Categories (Capacity Retention)
1. **Healthy / Normal Aging ($\text{SOH} \ge 90\%$):** Normal operating regime; linear degradation trajectory.
2. **Degraded Subpopulation ($80\% \le \text{SOH} < 90\%$):** Approaching degradation knee; increased variance.
3. **Critical Knee Regime ($\text{SOH} < 80\%$):** Primary lifecycle retirement threshold reached; non-linear acceleration.

### RUL Categories (Remaining Useful Cycles)
1. **Early-Life ($\text{RUL} \ge 800$ cycles):** Long remaining lifespan; higher trajectory uncertainty without future leakage.
2. **Mid-Life ($300 \le \text{RUL} < 800$ cycles):** Moderate remaining life; reliable trajectory tracking.
3. **Near End-of-Life ($\text{RUL} < 300$ cycles):** High operational precision; safe advance retirement window.
