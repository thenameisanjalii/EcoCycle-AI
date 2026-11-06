# EcoCycle AI — Task 2M.1: Advanced Model Design & Hyperparameter Optimization Plan

**Document ID:** ECOCYCLE-REPORT-TASK-2M-1-DESIGN-001  
**Pipeline Stage:** Task 2M.1 — Advanced Model Design & Static Audit  
**Execution Date:** 2026-09-07  
**Author:** EcoCycle AI Automated Modeling Engine  
**Status:** APPROVED DESIGN & STATIC AUDIT ONLY (NO MODELS TRAINED)  
**Raw Dataset SHA-256:** `0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88` (Verified Byte-Identical)  
**Test Partition Quarantine Status:** **STRICTLY QUARANTINED — ZERO TEST SET ACCESS**  

---

## 1. Executive Summary

Task 2M.1 establishes the formal technical specification, causal feature architecture, and reproducible hyperparameter optimization protocol for the **Advanced Modeling Stage** of the EcoCycle AI battery degradation pipeline.

Following the successful completion and independent verification of Task 2L.3, the project now transitions from baseline benchmarks to state-of-the-art gradient boosting frameworks:
1. **XGBoost Regressor** (`xgboost` 3.2.0)
2. **LightGBM Regressor** (`lightgbm` 4.7.0)
3. **CatBoost Regressor** (`catboost` 1.2.10)

Task 2M.1 is strictly restricted to **design, architectural planning, causality verification, and static auditing**. No advanced models have been trained, no hyperparameters have been fitted, and the Test partition remains **100% quarantined**.

---

## 2. Current Baseline Benchmark (Locked Immutable Records)

The winning baseline models from Task 2L.3 are locked as immutable comparative benchmarks. Advanced models developed in Task 2M must achieve a meaningful and statistically significant reduction in Validation RMSE to supersede these baselines:

| Target | Locked Baseline Benchmark | Validation MAE | Validation RMSE | Validation $R^2$ | Test MAE | Test RMSE | Test $R^2$ | Designation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOH (%)** | `soh_hist_gradient_boosting` | 0.4245% | **0.6805%** | 0.9818 | 0.3442% | **0.5896%** | 0.9815 | FINAL BASELINE WINNERS — NOT FINAL PRODUCTION MODELS |
| **RUL (cyc)** | `rul_hist_gradient_boosting` | 130.99 | **247.95** | 0.5440 | 113.79 | **174.33** | 0.8449 | FINAL BASELINE WINNERS — NOT FINAL PRODUCTION MODELS |

> [!IMPORTANT]
> **Preservation & Benchmark Rule:** Existing baseline model binaries (`models/baseline/soh_hist_gradient_boosting.joblib` and `rul_hist_gradient_boosting.joblib`) are designated as **FINAL BASELINE WINNERS — NOT FINAL PRODUCTION MODELS**. They will never be overwritten. Advanced models will reside in dedicated directories (`artifacts/models/task_2m/`).

---

## 3. Advanced Modeling Objectives

The primary objective of Task 2M is to determine whether advanced gradient boosting architectures combined with causal second-order and historical trajectory features can:
1. **SOH Regression:** Reduce Validation RMSE from **0.6805%** toward $< 0.60\%$, specifically refining prediction accuracy in the degraded knee regime ($\text{SOH} < 90\%$).
2. **RUL Regression:** Reduce Validation RMSE from **247.95 cycles** toward $< 200$ cycles, with targeted error reduction in early life ($\text{RUL} \ge 800$ cycles).
3. **Maintain Perfect Causality & Generalization:** Ensure zero leakage, zero test data contamination, and robust generalization across physically unseen battery cells.

---

## 4. Candidate Architectures & Technical Rationale

Three distinct gradient boosting paradigms will be evaluated alongside the scikit-learn baseline:

### 4.1 XGBoost Regressor (`xgb.XGBRegressor`)
- **Mathematical Foundation:** Exact and histogram-binned 2nd-order Taylor expansion of the loss function.
- **Regularization Capabilities:** Explicit $L_1$ (`reg_alpha`) and $L_2$ (`reg_lambda`) penalties on leaf weights.
- **Why Evaluated:** Battery sensor telemetry exhibits multicollinearity (e.g., lagged IR vs current IR) and localized sensor noise. XGBoost's leaf weight shrinkage and conservative tree pruning (`gamma`) prevent fitting spurious cycle-to-cycle impedance spikes.

### 4.2 LightGBM Regressor (`lgb.LGBMRegressor`)
- **Mathematical Foundation:** Leaf-wise (best-first) tree growth with histogram discretization of continuous variables.
- **Computational Efficiency:** Gradient-based One-Side Sampling (GOSS) and Exclusive Feature Bundling (EFB).
- **Why Evaluated:** Degradation curves are non-linear; the onset of the aging knee involves localized structural shifts that level-wise trees approximate inefficiently. Leaf-wise splitting allows deep refinement along critical degradation paths while controlling overall complexity via `num_leaves` and `min_child_samples`.

### 4.3 CatBoost Regressor (`cb.CatBoostRegressor`)
- **Mathematical Foundation:** Oblivious (symmetric) decision trees with ordered boosting.
- **Inductive Bias:** Symmetric tree structures evaluate identical split features at each tree depth, acting as a built-in structural regularizer.
- **Why Evaluated:** Standard gradient boosting creates prediction shift on sequential tabular time series. CatBoost's ordered boosting calculates leaf values using independent data subsets, offering superior robustness when evaluating across completely unseen battery cells.

---

## 5. Advanced Causal Feature Engineering Strategy

To decouple algorithmic improvements from feature representation gains, Task 2M establishes a **two-tier experimental design**:
- **Feature Set A (17 Baseline Features):** Identical to Task 2L, enabling clean architectural comparisons (XGBoost vs LightGBM vs CatBoost vs HistGradientBoosting).
- **Feature Set B (32 Advanced Features):** 17 baseline features augmented with 15 candidate causal degradation features.

### The 15 Candidate Causal Features:
1. **Second-Order Rates of Change (Acceleration):**
   - `IR_accel` = $\Delta \text{IR}(t) - \Delta \text{IR}(t-1)$
   - `QCharge_accel` = $\Delta \text{QCharge}(t) - \Delta \text{QCharge}(t-1)$
   - `Tavg_accel` = $\Delta \text{Tavg}(t) - \Delta \text{Tavg}(t-1)$
   - `chargetime_accel` = $\Delta \text{chargetime}(t) - \Delta \text{chargetime}(t-1)$
2. **Physical Degradation Ratios:**
   - `thermal_dissipation_rate` = $(T_{\text{max}}(t) - T_{\text{min}}(t)) / \max(\text{chargetime}(t), 0.01)$
   - `charge_efficiency_proxy` = $Q_{\text{Charge}}(t) / \max(\text{chargetime}(t), 0.01)$
   - `resistance_growth_ratio` = $\text{IR}(t) / \max(\text{IR\_lag1}(t), 10^{-6})$
3. **Past-Only Historical Rolling Statistics (Window = 5 Cycles):**
   - `IR_roll_mean_5`, `IR_roll_std_5`
   - `QCharge_roll_mean_5`, `QCharge_roll_std_5`
   - `Tavg_roll_mean_5`, `Tavg_roll_std_5`
4. **Early-Life Cumulative Trajectory Slopes:**
   - `cum_capacity_fade_rate` = $(Q_{\text{Charge}}(1) - Q_{\text{Charge}}(t)) / \max(\text{cycle}(t) - 1, 1)$
   - `cum_resistance_growth_rate` = $(\text{IR}(t) - \text{IR}(1)) / \max(\text{cycle}(t) - 1, 1)$

---

## 6. Formal Causality Audit & Temporal Proofs

Every candidate feature has undergone rigorous temporal causality auditing:

$$\forall \text{ Feature } f, \quad f(t) = \mathcal{F}\Big(\big\{ X_b(i) \mid i \le t \big\}\Big)$$

| Feature Name | Temporal Horizon | Causal Proof | Status |
| :--- | :---: | :--- | :---: |
| `IR_accel` | $[t-2, t]$ | Uses only cycles $t, t-1, t-2 \le t$. Zero future lookahead. | **CERTIFIED** |
| `QCharge_accel` | $[t-2, t]$ | Uses only cycles $t, t-1, t-2 \le t$. Zero future lookahead. | **CERTIFIED** |
| `Tavg_accel` | $[t-2, t]$ | Uses only cycles $t, t-1, t-2 \le t$. Zero future lookahead. | **CERTIFIED** |
| `chargetime_accel` | $[t-2, t]$ | Uses only cycles $t, t-1, t-2 \le t$. Zero future lookahead. | **CERTIFIED** |
| `thermal_dissipation_rate` | $[t]$ | Instantaneous cycle $t$ telemetry only. | **CERTIFIED** |
| `charge_efficiency_proxy` | $[t]$ | Instantaneous cycle $t$ telemetry only. | **CERTIFIED** |
| `resistance_growth_ratio` | $[t-1, t]$ | Uses cycle $t$ and cycle $t-1 \le t$. | **CERTIFIED** |
| `*_roll_mean_5` / `*_roll_std_5` | $[t-4, t]$ | Evaluated with `center=False` looking backwards. | **CERTIFIED** |
| `cum_capacity_fade_rate` | $[1, t]$ | References cycle 1 (birth) and cycle $t$. Does NOT use `max_cycle`. | **CERTIFIED** |
| `cum_resistance_growth_rate` | $[1, t]$ | References cycle 1 (birth) and cycle $t$. Does NOT use `max_cycle`. | **CERTIFIED** |

### Prohibited Operations:
- Centered rolling windows (`center=True`): **REJECTED**
- Future shifts (`shift(-k)`): **REJECTED**
- Future backward fill (`bfill`): **REJECTED**
- Total lifespan indicators (`max_cycle`, `final_cycle`): **REJECTED**

---

## 7. RUL Early-Life Degradation Investigation

Diagnostics from Task 2L.3 revealed a pronounced error disparity across RUL lifecycle stages:
- **Near-EOL ($\text{RUL} < 300$):** MAE = **55.76 cycles**
- **Mid-Life ($300 \le \text{RUL} < 800$):** MAE = **115.61 cycles**
- **Early-Life ($\text{RUL} \ge 800$):** MAE = **196.29 cycles**

### Physical Root Cause:
During the initial 100 cycles, cells with vastly different total lifespans (e.g., 700 cycles vs 1,900 cycles) exhibit almost identical instantaneous capacity ($SOH \approx 99\%$) and resistance ($IR \approx 0.016\,\Omega$). Instantaneous features alone cannot resolve cell durability kinetics.

### Causal Solution:
The newly designed cumulative features (`cum_capacity_fade_rate` and `cum_resistance_growth_rate`) calculate the per-cycle degradation rate from beginning-of-life ($cycle=1$) up to cycle $t$. By cycle 50, a cell fading at $0.02\,\text{mAh/cycle}$ is clearly distinguished from a cell fading at $0.005\,\text{mAh/cycle}$, providing the model with early trajectory curvature **without leaking final lifespan**.

---

## 8. Hyperparameter Search Strategy

A systematic, reproducible hyperparameter search using `RandomizedSearchCV` is established:
- **Search Method:** Randomized Search with 20 iterations per model family.
- **Validation Scheme:** `PredefinedSplit` mapping Train (81,545 rows / 97 cells) and Validation (16,606 rows / 21 cells).
- **Early Stopping:** 25 rounds on Validation RMSE to prevent over-fitting and optimize compute.
- **Fixed Random State:** `random_state = 42` across all libraries.

### Search Parameter Distributions:
```python
# XGBoost
{
    'n_estimators': [100, 150, 200, 300],
    'learning_rate': [0.03, 0.05, 0.08, 0.1],
    'max_depth': [4, 6, 8],
    'subsample': [0.7, 0.85, 1.0],
    'colsample_bytree': [0.7, 0.85, 1.0],
    'reg_alpha': [0.0, 0.1, 0.5, 1.0],
    'reg_lambda': [1.0, 3.0, 5.0, 10.0],
    'min_child_weight': [1, 3, 5]
}

# LightGBM
{
    'n_estimators': [100, 150, 200, 300],
    'learning_rate': [0.03, 0.05, 0.08, 0.1],
    'num_leaves': [20, 31, 63, 127],
    'max_depth': [-1, 6, 8, 10],
    'min_child_samples': [20, 50, 100],
    'subsample': [0.7, 0.85, 1.0],
    'colsample_bytree': [0.7, 0.85, 1.0],
    'reg_alpha': [0.0, 0.1, 0.5, 1.0],
    'reg_lambda': [1.0, 3.0, 5.0, 10.0]
}

# CatBoost
{
    'iterations': [150, 250, 350, 500],
    'learning_rate': [0.03, 0.05, 0.08, 0.1],
    'depth': [4, 6, 8],
    'l2_leaf_reg': [1.0, 3.0, 5.0, 10.0],
    'subsample': [0.8, 1.0]
}
```

---

## 9. Evaluation Metrics & Model Selection Policy

### Selection Hierarchy:
1. **Primary Selection Metric:** **Validation RMSE** (lowest is best).
2. **Secondary Metrics:** Validation MAE, Validation $R^2$.
3. **Meaningful Improvement Threshold:**
   - **SOH:** Advanced model must achieve $\Delta\text{RMSE} \le -0.02\%$ relative to baseline ($0.6805\%$).
   - **RUL:** Advanced model must achieve $\Delta\text{RMSE} \le -10.0\text{ cycles}$ relative to baseline ($247.95\text{ cyc}$).

---

## 10. Strict Leakage Prevention & Forbidden Columns

The following entities are strictly banned from feature matrices $X$:
- `battery_id`: Permitted ONLY as grouping metadata for splitting and diagnostics.
- `QDischarge`: Direct target leakage with SOH.
- Ground-truth `SOH` when predicting RUL.
- Ground-truth `RUL` when predicting SOH.
- `max_cycle`, `final_cycle`, `terminal_cycle`.
- Any future observations or symmetric rolling windows.

---

## 11. Data Partition & Test Quarantine Strategy

All model training and tuning in Task 2M will strictly utilize:
- **Train Partition:** 81,545 rows across 97 battery cells.
- **Validation Partition:** 16,606 rows across 21 battery cells.
- **Test Partition (Quarantined):** 18,512 rows across 21 battery cells.

> [!CAUTION]
> **Strict Quarantine Rule:** The Test partition must **NEVER** be accessed during hyperparameter optimization, model selection, or feature selection. It will only be opened once the winning advanced models are locked.

---

## 12. Reproducibility Protocol

- `random_state = 42` (and `random_seed = 42` for CatBoost) enforced across all model instantiations and CV splits.
- Deterministic histogram binning and thread controls.
- Full machine-readable tracking via `reports/modeling/task_2m_1_config.json`.

---

## 13. Artifact Registry

| Component | Target File | Purpose |
| :--- | :--- | :--- |
| Model Factory | `src/models/advanced_models.py` | Un-fitted XGBoost, LightGBM, CatBoost instantiations. |
| Tuning Config | `src/models/tuning_config.py` | Search spaces, CV configuration, and selection thresholds. |
| Feature Engineering | `src/models/feature_engineering.py` | Causal feature formulas, proofs, and transformation pipeline. |
| Static Audit Script | `test_task_2m_1_static_audit.py` | Independent verification of design consistency and quarantine. |
| Config JSON | `reports/modeling/task_2m_1_config.json` | Machine-readable specification. |
| Design Report | `reports/modeling/task_2m_1_advanced_model_design.md` | Formal engineering report. |

---

## 14. Static Audit Results

The independent audit script `test_task_2m_1_static_audit.py` executes 11 verification checks:
- Model configuration consistency: **PASS**
- Hyperparameter search configuration: **PASS**
- Feature leakage restrictions: **PASS**
- Causal feature definitions: **PASS**
- Train/Validation/Test boundaries: **PASS**
- Random seed consistency (42): **PASS**
- Baseline preservation: **PASS**
- Forbidden feature exclusions: **PASS**
- Test quarantine enforcement: **PASS**
- Raw dataset SHA-256 byte-identity: **PASS**
- Advanced models un-fitted: **PASS**

---

## 15. Limitations & Boundary Conditions

1. **Test Set Inaccessibility:** Final test performance cannot and must not be predicted or reported during Task 2M.1.
2. **Computational Budget:** Hyperparameter tuning is constrained to 20 iterations per model to balance search thoroughness with workstation compute limits.
3. **No Deep Learning Yet:** Task 2M focuses on advanced gradient boosting; neural networks (e.g. LSTM/Transformer) remain scoped for subsequent stages if boosting plateaus.

---

## 16. Approval Gate for Task 2M.2

All requirements for Task 2M.1 have been completed. The design, code modules, and static audits are fully established.

```
==================================================
TASK 2M.1 STATUS
==================================================

Advanced model design: PASS
Feature engineering design: PASS
Hyperparameter search design: PASS
Leakage audit: PASS
Causal feature audit: PASS
Partition audit: PASS
Reproducibility audit: PASS
Baseline preservation: PASS
Test quarantine: PASS
Raw dataset modified: NO

Advanced models trained: NO

Task 2M.1: COMPLETE

NEXT STAGE:
TASK 2M.2 — ADVANCED MODEL TRAINING & HYPERPARAMETER OPTIMIZATION

Execution STOPPED.
==================================================
```
