# EcoCycle AI — Task 2M.2: Advanced Model Training & Hyperparameter Optimization Report

**Document ID:** ECOCYCLE-REPORT-TASK-2M-2-TRAINING-001  
**Pipeline Stage:** Task 2M.2 — Advanced Model Training & Hyperparameter Optimization  
**Execution Date:** 2026-09-07  
**Author:** EcoCycle AI Automated Modeling Engine  
**Status:** COMPLETE — PROVISIONAL ADVANCED CANDIDATES SELECTED (TEST QUARANTINED)  
**Raw Dataset SHA-256:** `0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88` (Verified Byte-Identical)  
**Test Partition Quarantine Status:** **STRICTLY QUARANTINED — ZERO TEST SET ACCESS**  

---

## 1. Executive Summary

In **Task 2M.2**, twelve experimental configurations were systematically trained and optimized across three state-of-the-art gradient boosting frameworks (**XGBoost**, **LightGBM**, and **CatBoost**), evaluating both **Feature Set A (17 baseline features)** and **Feature Set B (32 advanced causal features)**.

All training utilized strictly the approved **Train partition (81,545 rows across 97 batteries)** and was evaluated exclusively against the **Validation partition (16,606 rows across 21 batteries)** using battery-grouped `PredefinedSplit`. The **Test partition (18,512 rows across 21 batteries) remained strictly quarantined** with zero access throughout tuning.


### Provisional Advanced Winners:

- **SOH Provisional Winner:** `soh_xgboost_32f` (XGBOOST on 32f)
  - Validation RMSE: **0.5654%** (vs Baseline Benchmark 0.6805%, $\Delta = +0.1151\%$, **+16.91% improvement**)
  - Validation MAE: **0.3347%** | Validation $R^2$: **0.9874**

- **RUL Provisional Winner:** `rul_catboost_32f` (CATBOOST on 32f)
  - Validation RMSE: **233.06 cycles** (vs Baseline Benchmark 247.95 cyc, $\Delta = +14.89\text{ cyc}$, **+6.01% improvement**)
  - Validation MAE: **129.42 cycles** | Validation $R^2$: **0.5971**

> [!IMPORTANT]

> **Candidate Designation:** These models are designated as **PROVISIONAL ADVANCED CANDIDATES**. They are NOT final models. Final model selection and subsequent final test evaluation will occur only in subsequent tasks under formal approval.


---

## 2. Full Experimental Results Matrix (12 Configurations)

| Config ID | Target | Model | Features | Val RMSE | Val MAE | Val $R^2$ | Base RMSE | $\Delta$ RMSE | % Improvement | Tuning Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `soh_xgboost_17f` | SOH | xgboost | 17f (17f) | **0.6522%** | 0.4054% | 0.9833 | 0.6805% | +0.0283% | **+4.15%** | 11.1s |
| `soh_lightgbm_17f` | SOH | lightgbm | 17f (17f) | **0.6481%** | 0.4051% | 0.9835 | 0.6805% | +0.0324% | **+4.75%** | 9.3s |
| `soh_catboost_17f` | SOH | catboost | 17f (17f) | **0.7016%** | 0.4539% | 0.9806 | 0.6805% | -0.0211% | **-3.10%** | 32.2s |
| `soh_xgboost_32f` | SOH | xgboost | 32f (32f) | **0.5654%** | 0.3347% | 0.9874 | 0.6805% | +0.1151% | **+16.91%** | 24.6s |
| `soh_lightgbm_32f` | SOH | lightgbm | 32f (32f) | **0.5799%** | 0.3491% | 0.9868 | 0.6805% | +0.1006% | **+14.79%** | 15.7s |
| `soh_catboost_32f` | SOH | catboost | 32f (32f) | **0.5949%** | 0.3760% | 0.9861 | 0.6805% | +0.0856% | **+12.58%** | 91.1s |
| `rul_xgboost_17f` | RUL | xgboost | 17f (17f) | **233.3249 cyc** | 131.2492 cyc | 0.5962 | 247.9500 cyc | +14.6251 cyc | **+5.90%** | 16.0s |
| `rul_lightgbm_17f` | RUL | lightgbm | 17f (17f) | **238.4520 cyc** | 128.4068 cyc | 0.5782 | 247.9500 cyc | +9.4980 cyc | **+3.83%** | 12.7s |
| `rul_catboost_17f` | RUL | catboost | 17f (17f) | **240.6258 cyc** | 131.9326 cyc | 0.5705 | 247.9500 cyc | +7.3242 cyc | **+2.95%** | 33.0s |
| `rul_xgboost_32f` | RUL | xgboost | 32f (32f) | **238.9821 cyc** | 133.4837 cyc | 0.5764 | 247.9500 cyc | +8.9679 cyc | **+3.62%** | 18.4s |
| `rul_lightgbm_32f` | RUL | lightgbm | 32f (32f) | **244.9543 cyc** | 133.2427 cyc | 0.5549 | 247.9500 cyc | +2.9957 cyc | **+1.21%** | 13.6s |
| `rul_catboost_32f` | RUL | catboost | 32f (32f) | **233.0551 cyc** | 129.4164 cyc | 0.5971 | 247.9500 cyc | +14.8949 cyc | **+6.01%** | 47.4s |

---

## 3. SOH Regression: Detailed Analysis & Model Ranking

Baseline benchmark: `soh_hist_gradient_boosting` (Val RMSE = **0.6805%**, Val MAE = 0.4245%, Val $R^2$ = 0.9818)

| Rank | Configuration | Val RMSE (%) | Val MAE (%) | Val $R^2$ | $\Delta$ vs Baseline | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `soh_xgboost_32f` | **0.5654%** | 0.3347% | 0.9874 | +0.1151% (+16.91%) | **PROVISIONAL WINNER** |
| 2 | `soh_lightgbm_32f` | **0.5799%** | 0.3491% | 0.9868 | +0.1006% (+14.79%) | Candidate |
| 3 | `soh_catboost_32f` | **0.5949%** | 0.3760% | 0.9861 | +0.0856% (+12.58%) | Candidate |
| 4 | `soh_lightgbm_17f` | **0.6481%** | 0.4051% | 0.9835 | +0.0324% (+4.75%) | Candidate |
| 5 | `soh_xgboost_17f` | **0.6522%** | 0.4054% | 0.9833 | +0.0283% (+4.15%) | Candidate |
| 6 | `soh_catboost_17f` | **0.7016%** | 0.4539% | 0.9806 | -0.0211% (-3.10%) | Candidate |

---

## 4. RUL Regression: Detailed Analysis & Model Ranking

Baseline benchmark: `rul_hist_gradient_boosting` (Val RMSE = **247.95 cycles**, Val MAE = 130.99 cycles, Val $R^2$ = 0.5440)

| Rank | Configuration | Val RMSE (cyc) | Val MAE (cyc) | Val $R^2$ | $\Delta$ vs Baseline | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `rul_catboost_32f` | **233.06** | 129.42 | 0.5971 | +14.89 cyc (+6.01%) | **PROVISIONAL WINNER** |
| 2 | `rul_xgboost_17f` | **233.32** | 131.25 | 0.5962 | +14.63 cyc (+5.90%) | Candidate |
| 3 | `rul_lightgbm_17f` | **238.45** | 128.41 | 0.5782 | +9.50 cyc (+3.83%) | Candidate |
| 4 | `rul_xgboost_32f` | **238.98** | 133.48 | 0.5764 | +8.97 cyc (+3.62%) | Candidate |
| 5 | `rul_catboost_17f` | **240.63** | 131.93 | 0.5705 | +7.32 cyc (+2.95%) | Candidate |
| 6 | `rul_lightgbm_32f` | **244.95** | 133.24 | 0.5549 | +3.00 cyc (+1.21%) | Candidate |

---

## 5. Feature Set A vs Feature Set B: Impact Decomposition

By comparing each model architecture under Feature Set A (17 features) versus Feature Set B (32 features), we directly isolate the impact of the newly engineered causal features:

| Model Family | Target | 17f Val RMSE | 32f Val RMSE | Feature Engineering Delta | Feature Engineering Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| XGBOOST | SOH | 0.6522% | 0.5654% | +0.0868% | Improved by +13.31% |
| LIGHTGBM | SOH | 0.6481% | 0.5799% | +0.0682% | Improved by +10.52% |
| CATBOOST | SOH | 0.7016% | 0.5949% | +0.1067% | Improved by +15.21% |
| XGBOOST | RUL | 233.3249 cyc | 238.9821 cyc | -5.6572 cyc | No gain (-2.42%) |
| LIGHTGBM | RUL | 238.4520 cyc | 244.9543 cyc | -6.5023 cyc | No gain (-2.73%) |
| CATBOOST | RUL | 240.6258 cyc | 233.0551 cyc | +7.5707 cyc | Improved by +3.15% |

---

## 6. RUL Negative Prediction Audit

In strict adherence to physical validation guidelines, predictions were evaluated **completely raw without artificial post-hoc clipping**:

| Configuration | Negative Pred Count | Negative Pred % | Min Prediction | Max Prediction | Clipping Applied |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `rul_catboost_32f` | 137 | 0.82% | -117.65 | 1143.56 | **NONE (Raw Unclipped)** |
| `rul_xgboost_17f` | 37 | 0.22% | -77.53 | 1104.55 | **NONE (Raw Unclipped)** |
| `rul_lightgbm_17f` | 33 | 0.20% | -7.45 | 1086.92 | **NONE (Raw Unclipped)** |
| `rul_xgboost_32f` | 26 | 0.16% | -69.38 | 1092.24 | **NONE (Raw Unclipped)** |
| `rul_catboost_17f` | 100 | 0.60% | -104.15 | 1058.22 | **NONE (Raw Unclipped)** |
| `rul_lightgbm_32f` | 96 | 0.58% | -17.12 | 1112.98 | **NONE (Raw Unclipped)** |

---

## 7. Hyperparameter Configurations of Best Candidates

### Best SOH Candidate:

```json
{
  "subsample": 0.7,
  "reg_lambda": 1.0,
  "reg_alpha": 0.1,
  "n_estimators": 150,
  "min_child_weight": 5,
  "max_depth": 8,
  "learning_rate": 0.08,
  "colsample_bytree": 0.85
}
```

### Best RUL Candidate:

```json
{
  "subsample": 0.8,
  "learning_rate": 0.1,
  "l2_leaf_reg": 5.0,
  "iterations": 500,
  "depth": 4
}
```


---

## 8. Artifact Registry

| Artifact Category | File Path | Description |
| :--- | :--- | :--- |
| **Results CSV** | `reports/modeling/task_2m_2/advanced_training_results.csv` | Full metric table across all 12 configurations. |
| **Results JSON** | `reports/modeling/task_2m_2/advanced_training_results.json` | Machine-readable hyperparameters and evaluation metrics. |
| **Best SOH Candidate** | `reports/modeling/task_2m_2/best_soh_candidate.json` | Top SOH model metadata. |
| **Best RUL Candidate** | `reports/modeling/task_2m_2/best_rul_candidate.json` | Top RUL model metadata. |
| **Validation Predictions** | `reports/modeling/task_2m_2/predictions/` | 12 CSV files containing raw predictions on 16,606 validation rows. |
| **Model Binaries** | `artifacts/models/task_2m/` | 12 trained Joblib models partitioned by target and architecture. |

---

## 9. Final Stage Verdict

```

==================================================
TASK 2M.2 STATUS
==================================================
Training: PASS
Configurations attempted: 12/12

SOH:
Best provisional model: soh_xgboost_32f
Feature set: 32f (32 features)
Validation RMSE: 0.5654%
Validation MAE: 0.3347%
Validation R²: 0.9874

RUL:
Best provisional model: rul_catboost_32f
Feature set: 32f (32 features)
Validation RMSE: 233.06 cycles
Validation MAE: 129.42 cycles
Validation R²: 0.5971

Baseline comparison:
SOH improvement: +0.1151% (+16.91%)
RUL improvement: +14.89 cycles (+6.01%)

Test partition accessed: NO
Raw dataset modified: NO
Leakage audit: PASS
Causal feature audit: PASS
Reproducibility audit: PASS
Artifact audit: PASS

Models are PROVISIONAL ADVANCED CANDIDATES.

Test evaluation: NOT PERFORMED

==================================================
```
