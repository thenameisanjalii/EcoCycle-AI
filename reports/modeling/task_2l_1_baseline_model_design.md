# EcoCycle AI — Task 2L.1: Baseline Model Design & Training Plan

**Document ID:** ECOCYCLE-REPORT-TASK-2L-1-DESIGN-001  
**Pipeline Stage:** Task 2L.1 — Baseline Model Design & Training Plan  
**Execution Date:** 2026-09-07  
**Author:** EcoCycle AI Automated Modeling Engine  
**Status:** DESIGN ONLY — NO MODELS TRAINED  
**Raw Dataset Path:** `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`  
**Raw Dataset SHA-256:** `0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88` (Locked & Untouched)  

---

## 1. Objective

The primary objective of **Task 2L.1** is to formulate a rigorous, defensible, and leakage-free baseline modeling strategy for two distinct supervised regression tasks:
1. **State of Health (SOH) Prediction**: Estimating battery capacity retention relative to nominal capacity.
2. **Remaining Useful Life (RUL) Prediction**: Forecasting the remaining number of operational charge/discharge cycles until reaching the nominal end-of-test life.

This stage establishes standard benchmark performance using simple, interpretable, and reproducible scikit-learn models prior to advanced model development or hyperparameter optimization.

---

## 2. Dataset Partitions & Battery Isolation

Modeling will be conducted strictly against the verified Task 2K processed datasets located in `data/processed/`:

| Partition | SOH File | RUL File | Rows | Batteries | Partition Role |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Train** | `train_soh.csv` | `train_rul.csv` | 81,545 | 97 | Model parameter fitting and scaler estimation only. |
| **Validation** | `val_soh.csv` | `val_rul.csv` | 16,606 | 21 | Model selection, candidate comparison, and metric reporting. |
| **Test** | `test_soh.csv` | `test_rul.csv` | 18,512 | 21 | Quarantined out-of-sample evaluation ONLY after model selection. |
| **Total** | — | — | **116,663** | **139** | Complete 100% dataset coverage with zero battery overlap. |

### Strict Group Isolation
- Intersection between Train, Validation, and Test battery IDs is strictly **0**.
- No battery appearing in Train will ever appear in Validation or Test.
- Random row-wise shuffling is strictly forbidden.

---

## 3. Target Definitions

### 3.1 SOH (State of Health)
- **Target Name:** `SOH`
- **Units:** Percentage (`%`)
- **Physical Meaning:** Current cycle discharge capacity relative to nominal capacity.
- **Handling Policy:** Continuous target. Values $>100\%$ remain unclipped to preserve genuine manufacturing over-capacity variance. Zero artificial categorization.

### 3.2 RUL (Remaining Useful Life)
- **Target Name:** `RUL`
- **Units:** Operational Cycles (`cycles`)
- **Physical Meaning:** $RUL_i = \max(\text{cycle}_{\text{battery}}) - \text{cycle}_i$.
- **Handling Policy:** Continuous integer target. No smoothing, no clipping. Exactly one terminal $RUL = 0$ record per battery.

---

## 4. Approved Feature Schema (Exactly 17 Features)

Both SOH and RUL baseline models will ingest exactly the 17 features approved in Task 2K:
1. `IR`: Measured cell internal resistance (Ohms).
2. `QCharge`: Total charge capacity for the cycle (Ah).
3. `Tavg`: Average operating cell temperature (°C).
4. `Tmax`: Maximum cell temperature during cycle (°C).
5. `Tmin`: Minimum cell temperature during cycle (°C).
6. `chargetime`: Total charging duration (min/s).
7. `cycle`: Monotonically increasing cycle index.
8. `IR_is_zero`: Binary flag indicating unmeasured zero-IR readings.
9. `temp_sensor_fault`: Binary flag indicating extreme thermal sensor clipping on Battery 85.
10. `IR_lag1`: Causal backward lag-1 internal resistance.
11. `IR_delta`: Single-step change $\Delta \text{IR} = \text{IR}_t - \text{IR}_{t-1}$.
12. `QCharge_lag1`: Causal backward lag-1 charge capacity.
13. `QCharge_delta`: Single-step change $\Delta Q = Q_t - Q_{t-1}$.
14. `Tavg_lag1`: Causal backward lag-1 average temperature.
15. `Tavg_delta`: Single-step change $\Delta T = T_t - T_{t-1}$.
16. `chargetime_lag1`: Causal backward lag-1 charge time.
17. `chargetime_delta`: Single-step change $\Delta t = t_t - t_{t-1}$.

---

## 5. Forbidden Features & Strict Leakage Boundaries

To prevent data leakage, the following fields are strictly excluded from the feature matrix $X$:
- `battery_id`: Grouping identifier only; never an ML feature.
- `QDischarge`: Collinear direct target leak with SOH (Pearson $r = 0.9989$). Strictly excluded.
- Ground-truth `SOH` in RUL models: Excluded to prevent indirect target leakage.
- `RUL` in SOH models: Excluded.
- Future-cycle terms (`max_cycle`, `final_cycle`, `terminal_cycle`): Excluded.
- Test/Validation-derived statistics: Never used in scalers or models.

---

## 6. Baseline Models Suite & Hyperparameters

Four baseline model architectures will be evaluated for both SOH and RUL:

### 1. Naive Baseline: `DummyRegressor(strategy='mean')`
- **Configuration:** `strategy='mean'`
- **Selection Rationale:** Establishes the non-informative empirical prior. Any viable ML model must decisively outperform this baseline.
- **Leakage Control:** Mean is computed strictly from the Training partition ($96.4608\%$ for SOH, $489.50$ cycles for RUL).

### 2. Linear Baseline: `Ridge(alpha=1.0, random_state=42)`
- **Configuration:** `alpha=1.0`, `random_state=42`
- **Pipeline:** Wrapped in `sklearn.pipeline.Pipeline([('scaler', RobustScaler()), ('model', Ridge(...))])`.
- **Selection Rationale:** Evaluates monotonic linear relationships with L2 regularization to stabilize collinear physical features.
- **Leakage Control:** `RobustScaler` is fitted strictly on `train_X` inside the pipeline.

### 3. Tree Ensemble: `RandomForestRegressor(...)`
- **Configuration:** `n_estimators=100`, `max_depth=15`, `min_samples_leaf=4`, `random_state=42`, `n_jobs=-1`
- **Selection Rationale:** Captures non-linear degradation curves and multi-feature interaction thresholds without manual feature transforms.
- **Overfitting Control:** Constrained tree depth (`max_depth=15`) and leaf regularization (`min_samples_leaf=4`) prevent individual tree memorization of the 81,545 training rows.

### 4. Gradient Boosting: `HistGradientBoostingRegressor(...)`
- **Configuration:** `max_iter=100`, `min_samples_leaf=20`, `random_state=42`
- **Selection Rationale:** State-of-the-art histogram-binned gradient boosted decision trees. Native support for large datasets with rapid convergence.
- **Leakage Control:** Strictly fit on Train partition.

---

## 7. Preprocessing & Scaling Strategy

- **Linear Models (`Ridge`)**: Require feature scaling because input magnitudes range from $10^{-3}$ Ohms (`IR`) to $10^3$ seconds (`chargetime`). `RobustScaler` (median / IQR) is selected because it resists extreme sensor observations without clipping.
- **Tree-Based Models (`RandomForest`, `HistGradientBoosting`)**: Invariant to monotonic scaling; ingest unscaled features directly.
- **Train-Only Fitting**: Preprocessing parameters are fitted strictly on `train_X`. Validation and Test sets are transformed using frozen train statistics.

---

## 8. Evaluation Metrics Rationale

Models will be evaluated across three complementary regression metrics:

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
   - *Physical Utility:* Provides intuitive, linear interpretation in true physical units (% for SOH, cycles for RUL). Reflects typical day-to-day error.

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
   - *Physical Utility:* Quadratically penalizes large errors. Critical in second-life battery qualification, where an unexpected large capacity drop or early failure presents severe safety and financial hazards.
   - *Selection Policy:* **Validation RMSE serves as the primary model selection criterion.**

3. **Coefficient of Determination ($R^2$)**:
   $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$
   - *Physical Utility:* Quantifies the proportion of target variance explained relative to the naive mean prior.

---

## 9. Validation Protocol & Model Selection Rule

1. Fit candidate baseline models strictly on the 97-battery Train partition.
2. Score all candidates on the 21-battery Validation partition.
3. Select the best performing model architecture per target based strictly on **minimum Validation RMSE**.
4. The 21-battery Test partition remains completely untouched and quarantined during this process.
5. Only after the candidate is locked will a single unbiased evaluation be performed on the Test set.

---

## 10. Planned Artifacts & Code Structure

The baseline implementation is organized cleanly within the project architecture:
- `src/models/config.py` — Centralized modeling parameters, schemas, and paths.
- `src/models/baseline_models.py` — Un-fitted baseline model factory constructors.
- `src/models/evaluation.py` — Standardized regression metric calculators.
- `reports/modeling/task_2l_1_config.json` — Serialized configuration.
- `reports/modeling/task_2l_1_baseline_model_design.md` — This design document.

---

## 11. Static Consistency Audit Results

A static consistency audit of this design was conducted against the processed datasets and Task 2K artifacts:
- **Feature Matrix Count:** Verified exactly 17 features present in `train_soh.csv` and `train_rul.csv`.
- **Forbidden Columns:** Confirmed `battery_id`, `QDischarge`, `SOH` (in RUL), and `RUL` (in SOH) are strictly excluded from $X$.
- **Target Columns:** Verified `SOH` and `RUL` targets match raw continuous distributions.
- **Dataset Paths:** Verified all 6 processed CSVs exist in `data/processed/`.
- **Preprocessors:** Verified `preprocessor_soh.joblib` and `preprocessor_rul.joblib` match Train continuous features.
- **Reproducibility:** Random seed is locked at `42` across all models.
- **Raw Dataset:** SHA-256 remains byte-identical (`0affa1f...`).
- **Models Trained:** **NONE (0 models trained during Task 2L.1)**.

---

## 12. Final Design Verdict

```
==================================================
TASK 2L.1 DESIGN VERDICT: PASS
==================================================
Baseline model suite fully specified.
Leakage boundaries, causal features, and validation protocols verified.
NO models trained in this stage.
Ready for Task 2L.2 upon user approval.
==================================================
```