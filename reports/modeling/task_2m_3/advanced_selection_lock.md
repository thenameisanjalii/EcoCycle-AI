# EcoCycle AI — Task 2M.3 Phase A: Advanced Model Selection Lock Record

**Document ID:** ECOCYCLE-REPORT-TASK-2M-3-SELECTION-LOCK-001  
**Pipeline Stage:** Task 2M.3 Phase A — Advanced Model Selection Lock  
**Execution Date:** 2026-09-07  
**Status:** **LOCKED & FORMALLY COMMITTED**  
**Quarantine Compliance:** **PASS — Test partition was NOT accessed prior to this lock.**  

---

## 1. Selection Protocol & Rule
- Advanced model selection is governed **strictly by Validation RMSE** on the 21-battery Validation partition (16,606 rows).
- The Test partition (18,512 rows across 21 batteries) remained **100% quarantined** during this phase.
- All 12 configurations trained in Task 2M.2 were audited and confirmed.

---

## 2. SOH Model Ranking (Validation RMSE)
| Rank | Configuration ID | Model | Features | Val RMSE (%) | Val MAE (%) | Val $R^2$ | Selection Decision |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `soh_xgboost_32f` | XGBoost | 32f | **0.5654%** | 0.3347% | 0.9874 | **LOCKED ADVANCED WINNER** |
| 2 | `soh_lightgbm_32f` | LightGBM | 32f | 0.5799% | 0.3491% | 0.9868 | Rejected |
| 3 | `soh_catboost_32f` | CatBoost | 32f | 0.5949% | 0.3760% | 0.9861 | Rejected |
| 4 | `soh_lightgbm_17f` | LightGBM | 17f | 0.6481% | 0.4051% | 0.9835 | Rejected |
| 5 | `soh_xgboost_17f` | XGBoost | 17f | 0.6522% | 0.4054% | 0.9833 | Rejected |
| 6 | `soh_catboost_17f` | CatBoost | 17f | 0.7016% | 0.4539% | 0.9806 | Rejected |

---

## 3. RUL Model Ranking (Validation RMSE)
| Rank | Configuration ID | Model | Features | Val RMSE (cyc) | Val MAE (cyc) | Val $R^2$ | Selection Decision |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `rul_catboost_32f` | CatBoost | 32f | **233.06** | 129.42 | 0.5971 | **LOCKED ADVANCED WINNER** |
| 2 | `rul_xgboost_17f` | XGBoost | 17f | 233.32 | 131.25 | 0.5962 | Rejected |
| 3 | `rul_lightgbm_17f` | LightGBM | 17f | 238.45 | 128.41 | 0.5782 | Rejected |
| 4 | `rul_xgboost_32f` | XGBoost | 32f | 238.98 | 133.48 | 0.5764 | Rejected |
| 5 | `rul_catboost_17f` | CatBoost | 17f | 240.63 | 131.93 | 0.5705 | Rejected |
| 6 | `rul_lightgbm_32f` | LightGBM | 32f | 244.95 | 133.24 | 0.5549 | Rejected |

---

## 4. Formal Selection Declaration
```
==================================================
PHASE A SELECTION LOCK: COMMITTED & APPROVED
SOH Winner: soh_xgboost_32f
RUL Winner: rul_catboost_32f
Criterion: Lowest Validation RMSE
Test quarantine prior to lock: PASS
Authorization: Test partition access granted for Phase B evaluation only.
==================================================
```
