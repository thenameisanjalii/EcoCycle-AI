# EcoCycle AI — Task 2L.2: Baseline Model Training & Validation Report

**Document ID:** ECOCYCLE-REPORT-TASK-2L-2-TRAINING-001  
**Pipeline Stage:** Task 2L.2 — Baseline Model Training & Validation  
**Execution Date:** 2026-09-07  
**Author:** EcoCycle AI Automated Modeling Engine  
**Status:** COMPLETE & VERIFIED  
**Raw Dataset Path:** `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`  
**Raw Dataset SHA-256:** `0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88` (Verified Byte-Identical)  
**Test Partition Quarantined:** **YES — NEVER ACCESSED**  

---

## 1. Executive Summary

In **Task 2L.2**, all eight contracted baseline models (4 for SOH, 4 for RUL) were trained strictly on the isolated **Train partition (81,545 rows, 97 batteries)** using the approved 17 causal features from Task 2K. Performance was evaluated exclusively against the **Validation partition (16,606 rows, 21 batteries)**.

### Strict Protocol Compliance:
- **Test Partition Quarantine:** Neither `test_soh.csv` nor `test_rul.csv` was opened, read, or evaluated.
- **Raw Dataset Intact:** Raw `master_dataset.csv` remains 100% byte-identical.
- **Feature Purity:** Zero forbidden features (`battery_id`, `QDischarge`, target leaks, lookahead terms) entered $X$.
- **Reproducibility:** All models trained with locked seed `random_state=42`.

---

## 2. SOH Baseline Performance & Model Comparison

Target: **`SOH` (%)** | Sorted by Validation RMSE ascending:

| Rank | Model Identifier | Architecture | Train Rows | Val Rows | Fit Time (s) | Val MAE (%) | Val RMSE (%) | Val $R^2$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `soh_hist_gradient_boosting` | Hist Gradient Boosting | 81,545 | 16,606 | 3.5057s | 0.4245% | **0.6805%** | **0.9818** |
| 2 | `soh_random_forest` | Random Forest (d=15) | 81,545 | 16,606 | 14.0988s | 0.4255% | **0.7047%** | **0.9805** |
| 3 | `soh_ridge` | Ridge + RobustScaler | 81,545 | 16,606 | 0.0743s | 0.8096% | **1.2373%** | **0.9398** |
| 4 | `soh_dummy` | Dummy Mean Prior | 81,545 | 16,606 | 0.0017s | 3.6626% | **5.0492%** | **-0.0024** |

### SOH Selection Finding:
- **Best Provisional SOH Model:** `soh_hist_gradient_boosting` with lowest Validation RMSE of **0.6805%** (Val MAE = 0.4245%, Val $R^2$ = 0.9818).
- Substantial improvement over reference Dummy baseline (RMSE reduced from 5.0492% to 0.6805%).

---

## 3. RUL Baseline Performance & Model Comparison

Target: **`RUL` (cycles)** | Sorted by Validation RMSE ascending:

| Rank | Model Identifier | Architecture | Train Rows | Val Rows | Fit Time (s) | Val MAE (cyc) | Val RMSE (cyc) | Val $R^2$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `rul_hist_gradient_boosting` | Hist Gradient Boosting | 81,545 | 16,606 | 0.9072s | 130.99 | **247.95** | **0.5440** |
| 2 | `rul_random_forest` | Random Forest (d=15) | 81,545 | 16,606 | 14.2852s | 135.90 | **257.51** | **0.5081** |
| 3 | `rul_ridge` | Ridge + RobustScaler | 81,545 | 16,606 | 0.0561s | 202.51 | **273.20** | **0.4463** |
| 4 | `rul_dummy` | Dummy Mean Prior | 81,545 | 16,606 | 0.0007s | 286.55 | **367.54** | **-0.0020** |

### RUL Selection Finding:
- **Best Provisional RUL Model:** `rul_hist_gradient_boosting` with lowest Validation RMSE of **247.95 cycles** (Val MAE = 130.99 cycles, Val $R^2$ = 0.5440).
- Substantial improvement over reference Dummy baseline (RMSE reduced from 367.54 to 247.95 cycles).

---

## 4. Sanity Checks & Integrity Verification

1. **NaN / Infinite Predictions:** Exactly 0 NaNs and 0 Infs across all 8 prediction sets.
2. **Prediction Alignment:** Exactly 16,606 prediction rows generated per model, matching validation rows.
3. **Battery Set Disjointness:** Train (97 batteries) and Validation (21 batteries) have exactly 0 overlap.
4. **Forbidden Feature Audit:** Confirmed `battery_id`, `QDischarge`, target leaks, and terminal-cycle terms are absent from $X$.
5. **Test Set Quarantine:** Test partition was completely quarantined and never accessed.
6. **Dummy Prior Correctness:** `soh_dummy` predicted exactly 96.4608% (Train SOH mean); `rul_dummy` predicted exactly 489.50 cycles (Train RUL mean).
7. **Raw Dataset Safety:** SHA-256 remains `0affa1f...`, 116,663 rows × 11 columns.

---

## 5. Artifacts Generated in Task 2L.2

### Code Modules:
- `src/models/train_baselines.py`
- `src/models/evaluate_baselines.py`

### Model Binaries (`models/baseline/`):
- `soh_dummy.joblib`
- `soh_ridge.joblib`
- `soh_random_forest.joblib`
- `soh_hist_gradient_boosting.joblib`
- `rul_dummy.joblib`
- `rul_ridge.joblib`
- `rul_random_forest.joblib`
- `rul_hist_gradient_boosting.joblib`

### Validation Prediction CSVs (`reports/modeling/predictions/`):
- `soh_dummy_validation.csv`
- `soh_ridge_validation.csv`
- `soh_random_forest_validation.csv`
- `soh_hist_gradient_boosting_validation.csv`
- `rul_dummy_validation.csv`
- `rul_ridge_validation.csv`
- `rul_random_forest_validation.csv`
- `rul_hist_gradient_boosting_validation.csv`

### Results & Summary:
- `reports/modeling/task_2l_2_baseline_results.csv`
- `reports/modeling/task_2l_2_baseline_results.json`
- `reports/modeling/task_2l_2_baseline_training_report.md`

---

## 6. Warnings & Baseline Limitations for Next Stage

1. **RUL Early-Cycle Horizon Uncertainty:** For high-cycle batteries (e.g. Battery 132, 1,934 cycles), baseline models underestimate initial life because early degradation signatures resemble standard 800-cycle cells.
2. **Negative Prediction Handling:** Linear Ridge generated unconstrained negative RUL predictions near end-of-life. Monotonic constraints and non-negative projections will be explored in advanced modeling.
3. **Hyperparameter Tuning:** Baseline models utilized conservative default parameters. Dedicated gradient boosting (XGBoost, LightGBM) and hyperparameter optimization will follow in Stage 2M.

---

```
==================================================
TASK 2L.2 STATUS
==================================================

Training completed: PASS
SOH models trained: 4/4
RUL models trained: 4/4
Validation evaluation: PASS
Test partition accessed: NO
Leakage audit: PASS
Raw dataset modified: NO
Reproducibility: PASS

Best provisional SOH model: soh_hist_gradient_boosting
Best provisional RUL model: rul_hist_gradient_boosting

Models trained: YES
Test evaluation: NOT PERFORMED

==================================================
```