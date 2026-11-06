# EcoCycle AI — Task 2L.3 Phase A: Baseline Model Selection Record

**Document ID:** ECOCYCLE-REPORT-TASK-2L-3-SELECTION-001  
**Pipeline Stage:** Task 2L.3 Phase A — Selection Lock  
**Execution Date:** 2026-09-07  
**Status:** LOCKED & FORMALLY APPROVED  

---

## 1. Selection Protocol & Rule

- Model ranking is governed **strictly by Validation RMSE** on the 21-battery Validation partition.
- Training set performance was not used for selection to prevent overfitting bias.
- Test partition was strictly quarantined and **NOT accessed** during selection.
- No hyperparameter tuning was conducted.

---

## 2. SOH Baseline Model Ranking

| Rank | Model Name | Val MAE (%) | Val RMSE (%) | Val $R^2$ | Selection Decision |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `soh_hist_gradient_boosting` | 0.4245% | **0.6805%** | 0.9818 | **LOCKED WINNER** |
| 2 | `soh_random_forest` | 0.4255% | **0.7047%** | 0.9805 | Rejected |
| 3 | `soh_ridge` | 0.8096% | **1.2373%** | 0.9398 | Rejected |
| 4 | `soh_dummy` | 3.6626% | **5.0492%** | -0.0024 | Rejected |

---

## 3. RUL Baseline Model Ranking

| Rank | Model Name | Val MAE (cyc) | Val RMSE (cyc) | Val $R^2$ | Selection Decision |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `rul_hist_gradient_boosting` | 130.99 | **247.95** | 0.5440 | **LOCKED WINNER** |
| 2 | `rul_random_forest` | 135.90 | **257.51** | 0.5081 | Rejected |
| 3 | `rul_ridge` | 202.51 | **273.20** | 0.4463 | Rejected |
| 4 | `rul_dummy` | 286.55 | **367.54** | -0.0020 | Rejected |

---

## 4. Formal Selection Lock Declaration

```
==================================================
PHASE A SELECTION LOCK: PASS
SOH Winner: soh_hist_gradient_boosting
RUL Winner: rul_hist_gradient_boosting
Criterion: Lowest Validation RMSE
Status: Models are FINAL BASELINE WINNERS — NOT FINAL PRODUCTION MODELS
Authorization: Test partition access granted for Phase B evaluation only.
==================================================
```