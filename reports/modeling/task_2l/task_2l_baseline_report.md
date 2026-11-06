# EcoCycle AI — Task 2L: Baseline Machine Learning Training & Evaluation Report

**Document ID:** ECOCYCLE-REPORT-TASK-2L-BASELINE-001  
**Author:** EcoCycle AI Automated Modeling Engine  
**Execution Date:** 2026-09-07  
**Pipeline Stage:** Task 2L — Baseline ML Training  
**Audit Status:** COMPLETE & VERIFIED  
**Final Verdict:** **PASS**

---

## 1. Executive Summary & Objective

The primary objective of **Task 2L** is to establish rigorous, reproducible, and leakage-free machine learning baselines for predicting:
1. **State of Health (SOH, %)**: battery capacity retention relative to nominal capacity.
2. **Remaining Useful Life (RUL, cycles)**: the remaining number of operational charge/discharge cycles until reaching the end-of-first-life threshold (defined as nominal end of test cycle life in this dataset).

To adhere strictly to industry-standard machine learning practices and avoid premature optimization:
- Four baseline model families were selected, trained, and evaluated for both targets:
  1. `DummyRegressor(strategy="mean")` — establishing the non-informative empirical prior.
  2. `Ridge(alpha=1.0)` with `RobustScaler` pipeline — establishing linear benchmark performance with outlier-resilient scaling.
  3. `RandomForestRegressor(n_estimators=100, max_depth=15, min_samples_leaf=4)` — establishing non-linear ensemble performance with constrained tree depth to prevent overfitting.
  4. `HistGradientBoostingRegressor(max_iter=100, min_samples_leaf=20)` — establishing modern gradient boosting performance with native histogram binning.
- **Model Selection Rule**: Model selection was governed strictly by **Validation RMSE** (on the locked 21-battery Validation partition).
- **Test Set Quarantine**: The 21-battery Test partition was completely quarantined during model training, pipeline fitting, and model selection. Only after the winning models were finalized was a single unbiased evaluation performed on the test set.

### Key Results Summary

| Target | Best Model Architecture | Train RMSE | Validation MAE | Validation RMSE | Validation $R^2$ | Test MAE | Test RMSE | Test $R^2$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SOH (%)** | `HistGradientBoostingRegressor` | 0.3262% | 0.4245% | **0.6805%** | **0.9818** | 0.3442% | **0.5896%** | **0.9815** |
| **RUL (cycles)** | `HistGradientBoostingRegressor` | 41.67 | 130.99 | **247.95** | **0.5440** | 113.79 | **174.33** | **0.8449** |

Both primary baseline targets selected `HistGradientBoostingRegressor` as the superior architecture on validation RMSE. The baseline models substantially outperform the dummy regressors (SOH Val RMSE improved from 5.0492% to 0.6805%; RUL Val RMSE improved from 367.54 to 247.95 cycles).

---

## 2. Datasets & Partition Verification

All training and evaluation operations were executed strictly against the preprocessed, feature-engineered artifacts generated during **Task 2K**, derived from the locked battery-grouped 70/15/15 split established in **Task 2I**.

### 2.1 Dataset Partition Dimensions & Hashes
The raw dataset was audited in read-only mode, and its SHA-256 hash was confirmed intact before and after execution:
- **Raw Dataset Path:** `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`
- **Raw SHA-256 Hash:** `0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88`
- **Raw Dimensions:** 116,663 rows × 11 columns

### 2.2 Task 2K Processed Artifact Inputs
| Dataset Partition | Target | Rows | Feature Columns ($X$) | Metadata Columns | Battery Count | Battery ID Set Coverage |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `train_soh.csv` | SOH | 81,545 | 17 | `battery_id`, `cycle` | 97 | Partition Train (Seed 42) |
| `val_soh.csv` | SOH | 16,606 | 17 | `battery_id`, `cycle` | 21 | Partition Validation (Seed 42) |
| `test_soh.csv` | SOH | 18,512 | 17 | `battery_id`, `cycle` | 21 | Partition Test (Seed 42) |
| `train_rul.csv` | RUL | 81,545 | 17 | `battery_id`, `cycle` | 97 | Partition Train (Seed 42) |
| `val_rul.csv` | RUL | 16,606 | 17 | `battery_id`, `cycle` | 21 | Partition Validation (Seed 42) |
| `test_rul.csv` | RUL | 18,512 | 17 | `battery_id`, `cycle` | 21 | Partition Test (Seed 42) |
| **Total** | — | **116,663** | — | — | **139** | Complete 100% Coverage |

Every feature matrix $X$ was verified to have zero missing values (`NaN = 0`) and zero infinite values (`Inf = 0`).

---

## 3. Feature Specification & Modeling Policy

Per the locked modeling contracts from **Task 2H** and **Task 2K**, the feature matrix $X$ consists of exactly 17 numerical and binary features:

### 3.1 The 17 Contracted Features
1. `IR` — Internal resistance (measured in Ohms).
2. `QCharge` — Total charge capacity per cycle (Ah).
3. `Tavg` — Average operating cell temperature (°C).
4. `Tmax` — Maximum cell temperature during cycle (°C).
5. `Tmin` — Minimum cell temperature during cycle (°C).
6. `chargetime` — Total charging duration (minutes/seconds).
7. `cycle` — Monotonically increasing cycle index.
8. `IR_is_zero` — Binary indicator flag for unmeasured / zero internal resistance.
9. `temp_sensor_fault` — Binary indicator flag for extreme sensor anomaly clipping.
10. `IR_lag1` — Backward-looking lag-1 internal resistance ($\mathrm{IR}_{t-1}$, forward-filled from cycle 1).
11. `IR_delta` — Single-step change $\Delta \mathrm{IR} = \mathrm{IR}_t - \mathrm{IR}_{t-1}$ (causal, 0 at $t=1$).
12. `QCharge_lag1` — Backward-looking lag-1 charge capacity ($Q_{\mathrm{charge}, t-1}$).
13. `QCharge_delta` — Single-step change $\Delta Q_{\mathrm{charge}} = Q_{\mathrm{charge}, t} - Q_{\mathrm{charge}, t-1}$.
14. `Tavg_lag1` — Backward-looking lag-1 average temperature ($T_{\mathrm{avg}, t-1}$).
15. `Tavg_delta` — Single-step change $\Delta T_{\mathrm{avg}} = T_{\mathrm{avg}, t} - T_{\mathrm{avg}, t-1}$.
16. `chargetime_lag1` — Backward-looking lag-1 charge time ($t_{\mathrm{charge}, t-1}$).
17. `chargetime_delta` — Single-step change $\Delta t_{\mathrm{charge}} = t_{\mathrm{charge}, t} - t_{\mathrm{charge}, t-1}$.

### 3.2 Preprocessing & Scaling Architecture
- **Tree-Based Models (`RandomForestRegressor`, `HistGradientBoostingRegressor`)**: Directly ingested the unscaled 17-feature matrix. Decision trees are invariant to monotonic transformations and preserve exact physical cutoffs.
- **Linear Models (`Ridge`)**: Encapsulated within an end-to-end `sklearn.pipeline.Pipeline`:
  ```python
  Pipeline([
      ('scaler', RobustScaler()),
      ('model', Ridge(alpha=1.0, random_state=42))
  ])
  ```
  The `RobustScaler` was fitted strictly on `train_X` and transformed `val_X` and `test_X` to prevent training-distribution leakage.

---

## 4. Target Variables & Units

Both targets were trained and evaluated strictly in their **natural physical units** without artificial scaling or logarithmic transformations:
1. **SOH Target (`SOH`)**:
   - Physical Unit: Percentage (`%`).
   - Range across Train: $[75.0396\%, 101.5639\%]$.
   - Train Mean: $96.4608\% \pm 4.4480\%$.
2. **RUL Target (`RUL`)**:
   - Physical Unit: Operational Cycles (`cycles`).
   - Range across Train: $[0, 2236]$ cycles.
   - Train Mean: $489.50 \pm 356.40$ cycles.
   - Predictions were evaluated directly against actual cycles without artificial post-hoc clamping to expose native architectural bias.

---

## 5. Strict Leakage Controls & Boundaries

To eliminate all forms of data leakage identified in Tasks 2G, 2H, and 2K:
1. **Zero Battery ID in Features**: `battery_id` was isolated exclusively as a grouping and aggregation key. It was never included in feature matrix $X$.
2. **Exclusion of `QDischarge`**: `QDischarge` is mathematically collinear with SOH ($SOH = Q_{\mathrm{discharge}} / Q_{\mathrm{nominal}} 	imes 100$) and was strictly excluded from both SOH and RUL feature sets.
3. **Target Isolation**: Ground-truth `SOH` was excluded from all RUL models, and `RUL` was excluded from all SOH models.
4. **Causal Directionality**: All lag and delta features were computed strictly backwards in time ($t - (t-1)$) per battery group. No centered or forward-looking windows were utilized.
5. **Partition Disjointness**: The battery IDs in Train (97), Validation (21), and Test (21) have exactly zero intersection:
   $$\mathrm{Train} \cap \mathrm{Validation} = \emptyset, \quad \mathrm{Train} \cap \mathrm{Test} = \emptyset, \quad \mathrm{Validation} \cap \mathrm{Test} = \emptyset$$

---

## 6. Baseline Model Architectures & Hyperparameters

| Target | Model Identifier | Model Class | Key Hyperparameters | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **SOH** | `soh_dummy` | `DummyRegressor` | `strategy="mean"` | Baseline null model predicting train mean ($96.4608\%$). |
| **SOH** | `soh_ridge` | `Pipeline(RobustScaler, Ridge)` | $lpha=1.0$, `random_state=42` | Regularized linear baseline resilient to feature magnitude differences. |
| **SOH** | `soh_random_forest` | `RandomForestRegressor` | `n_estimators=100`, `max_depth=15`, `min_samples_leaf=4`, `random_state=42`, `n_jobs=-1` | Non-linear ensemble baseline with constrained depth to mitigate overparameterization. |
| **SOH** | `soh_hist_gradient_boosting` | `HistGradientBoostingRegressor` | `max_iter=100`, `min_samples_leaf=20`, `random_state=42` | High-efficiency gradient boosted trees with binned split finding. |
| **RUL** | `rul_dummy` | `DummyRegressor` | `strategy="mean"` | Baseline null model predicting train mean ($489.50$ cycles). |
| **RUL** | `rul_ridge` | `Pipeline(RobustScaler, Ridge)` | $lpha=1.0$, `random_state=42` | Linear baseline assessing monotonic relationship between cycle/degradation and RUL. |
| **RUL** | `rul_random_forest` | `RandomForestRegressor` | `n_estimators=100`, `max_depth=15`, `min_samples_leaf=4`, `random_state=42`, `n_jobs=-1` | Non-linear ensemble model capturing non-linear capacity drop inflection points. |
| **RUL** | `rul_hist_gradient_boosting` | `HistGradientBoostingRegressor` | `max_iter=100`, `min_samples_leaf=20`, `random_state=42` | Fast gradient boosting baseline capturing complex multivariate degradation surfaces. |

---

## 7. Model Training & Evaluation Protocol

1. **Deterministic Training**: All models were instantiated with `random_state=42` and fit strictly on `train_X` (81,545 samples). Training wall-clock execution times were accurately profiled.
2. **Model Selection on Validation Only**: All four baseline candidates per target were evaluated on `val_X` (16,606 samples). The model achieving the minimum **Validation Root Mean Squared Error (RMSE)** was declared the winning baseline architecture.
3. **Quarantined Test Set Scoring**: The untouched `test_X` (18,512 samples) was evaluated only once per candidate model to observe out-of-distribution generalization to completely unseen batteries.

---

## 8. SOH Baseline Performance & Model Comparison

### 8.1 Performance Metrics Across All Partitions
Metrics are reported in natural physical units (% capacity retention):

| Model | Partition | Fit Time (s) | MAE (%) | RMSE (%) | $R^2$ | Pred Min (%) | Pred Max (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **soh_dummy** | Train | 0.004 | 3.2462 | 4.4480 | 0.0000 | 96.4608 | 96.4608 |
| | **Validation** | — | **3.6626** | **5.0492** | **-0.0024** | 96.4608 | 96.4608 |
| | Test | — | 3.1773 | 4.3331 | -0.0007 | 96.4608 | 96.4608 |
| **soh_ridge** | Train | 0.153 | 0.7502 | 1.3558 | 0.9071 | 77.3319 | 165.9955 |
| | **Validation** | — | **0.8096** | **1.2373** | **0.9398** | 78.1975 | 103.5874 |
| | Test | — | 0.6737 | 1.0491 | 0.9413 | 77.9168 | 105.9115 |
| **soh_random_forest** | Train | 18.992 | 0.0806 | 0.1849 | 0.9983 | 75.0396 | 101.5639 |
| | **Validation** | — | **0.4255** | **0.7047** | **0.9805** | 75.2322 | 100.8635 |
| | Test | — | 0.3710 | 0.6457 | 0.9778 | 75.5474 | 100.6131 |
| **soh_hist_gradient_boosting** | Train | 5.071 | 0.2033 | 0.3262 | 0.9946 | 75.2462 | 101.1844 |
| | **Validation** | — | **0.4245** | **0.6805** | **0.9818** | 75.8771 | 100.4540 |
| | Test | — | 0.3442 | 0.5896 | 0.9815 | 75.5601 | 100.6438 |

### 8.2 Observations on SOH Baselines
- **`soh_hist_gradient_boosting`** achieved the lowest Validation RMSE of **0.6805%**, slightly outperforming `soh_random_forest` (0.7047%) while training ~3.7× faster (5.07s vs 18.99s).
- On the unseen test set, `soh_hist_gradient_boosting` generalized remarkably well, achieving **0.3442% MAE**, **0.5896% RMSE**, and an $R^2$ of **0.9815**.
- Linear Ridge regression produced reasonable fits ($R^2 pprox 0.94$), but suffered from physical boundary violations (predicting maximum SOH of 165.99% on Train and 105.91% on Test). In contrast, both tree ensembles naturally bounded predictions within $[75.2\%, 101.2\%]$.

---


### 8.3 Inference Latency & Prediction Speed
All models exhibit ultra-fast prediction throughput on CPU:
- soh_dummy: 0.5 ms total (0.00003 ms/sample)
- soh_ridge: 10.5 ms total (0.00063 ms/sample)
- soh_hist_gradient_boosting: 76.9 ms total (0.00463 ms/sample)
- soh_random_forest: 98.7 ms total (0.00594 ms/sample)

## 9. RUL Baseline Performance & Model Comparison

### 9.1 Performance Metrics Across All Partitions
Metrics are reported in natural physical units (cycles):

| Model | Partition | Fit Time (s) | MAE (cyc) | RMSE (cyc) | $R^2$ | Pred Min | Pred Max | Pred < 0 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **rul_dummy** | Train | 0.006 | 280.94 | 356.40 | 0.0000 | 489.50 | 489.50 | 0 |
| | **Validation** | — | **286.55** | **367.54** | **-0.0020** | 489.50 | 489.50 | 0 |
| | Test | — | 332.06 | 446.72 | -0.0185 | 489.50 | 489.50 | 0 |
| **rul_ridge** | Train | 0.135 | 175.46 | 242.57 | 0.5367 | -1019.31 | 2350.83 | 3,806 |
| | **Validation** | — | **202.51** | **273.20** | **0.4463** | -596.04 | 1095.18 | 813 |
| | Test | — | 272.78 | 370.73 | 0.2986 | -938.59 | 1139.29 | 785 |
| **rul_random_forest** | Train | 24.342 | 7.55 | 16.29 | 0.9979 | 0.43 | 2232.34 | 0 |
| | **Validation** | — | **135.90** | **257.51** | **0.5081** | 0.44 | 1105.84 | 0 |
| | Test | — | 125.15 | 195.43 | 0.8051 | 0.44 | 1823.45 | 0 |
| **rul_hist_gradient_boosting** | Train | 2.201 | 30.30 | 41.67 | 0.9863 | -17.55 | 2204.43 | 57 |
| | **Validation** | — | **130.99** | **247.95** | **0.5440** | -49.27 | 1148.98 | 49 |
| | Test | — | 113.79 | 174.33 | 0.8449 | -7.68 | 1949.29 | 26 |

### 9.2 Observations on RUL Baselines
- **`rul_hist_gradient_boosting`** achieved the lowest Validation RMSE of **247.95 cycles** and highest Validation $R^2$ of **0.5440**, outperforming `rul_random_forest` (RMSE 257.51 cycles).
- On the unseen test set, `rul_hist_gradient_boosting` reached **113.79 cycles MAE**, **174.33 cycles RMSE**, and an $R^2$ of **0.8449**.
- **Negative Prediction Audit**:
  - `rul_ridge` suffered catastrophic negative predictions due to linear extrapolation past zero degradation, producing 813 negative predictions on Validation (minimum -596 cycles).
  - `rul_random_forest` produced exactly **0 negative predictions** across all sets because tree leaves are bounded by training sample targets ($[0.43, 2232.34]$).
  - `rul_hist_gradient_boosting` produced a small number of slightly negative predictions near end-of-life (49 rows on Validation, 0.29% of samples; min -49.27 cycles) due to unconstrained leaf gradient steps.

---


### 9.3 RUL Inference Latency & Prediction Speed
- 
ul_dummy: 0.1 ms total (0.00001 ms/sample)
- 
ul_ridge: 7.9 ms total (0.00048 ms/sample)
- 
ul_hist_gradient_boosting: 84.8 ms total (0.00511 ms/sample)
- 
ul_random_forest: 70.6 ms total (0.00425 ms/sample)

## 10. Model Selection Decision & Rationale

Per the strict modeling protocol, selection was based **strictly on minimum Validation RMSE**:
1. **SOH Winner:** `soh_hist_gradient_boosting`
   - Validation RMSE: **0.6805%** (vs. 0.7047% RF, 1.2373% Ridge, 5.0492% Dummy).
   - Validation MAE: **0.4245%**.
   - Training time: **5.07s** (substantially faster than Random Forest's 18.99s).
2. **RUL Winner:** `rul_hist_gradient_boosting`
   - Validation RMSE: **247.95 cycles** (vs. 257.51 cycles RF, 273.20 cycles Ridge, 367.54 cycles Dummy).
   - Validation MAE: **130.99 cycles**.
   - Training time: **2.20s** (11× faster than Random Forest's 24.34s).

Both winning models were promoted to primary baseline status and subjected to granular error, cohort, and battery-level diagnostic profiling.

---

## 11. Selected SOH Model Deep Dive (`soh_hist_gradient_boosting`)

### 11.1 Error Breakdown Across SOH Operating Ranges (Validation Set)
To understand performance across healthy vs degraded regimes, validation predictions were binned into four standard battery health brackets:

| Operating Health Range | Sample Count | Percentage | Actual Mean SOH | Pred Mean SOH | MAE (%) | RMSE (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy ($\mathrm{SOH} \ge 95\%$)** | 12,396 | 74.6% | 98.67% | 98.56% | **0.3232%** | **0.5039%** |
| **Normal ($90\% \le \mathrm{SOH} < 95\%$)** | 2,122 | 12.8% | 92.92% | 93.02% | **0.6230%** | **0.8672%** |
| **Degraded ($80\% \le \mathrm{SOH} < 90\%$)** | 1,830 | 11.0% | 86.00% | 86.13% | **0.7314%** | **1.0461%** |
| **Critical End-of-Life ($\mathrm{SOH} < 80\%$)** | 258 | 1.6% | 77.71% | 78.89% | **1.4802%** | **1.9126%** |

### 11.2 SOH Error Analysis & Residual Distribution
- In the healthy regime ($\mathrm{SOH} \ge 95\%$), which comprises 74.6% of operational cycles, the model is exceptionally precise with an MAE of **0.32%**.
- Error gradually increases as the battery degrades into the non-linear "knee point" regime ($\mathrm{SOH} < 80\%$), where MAE reaches **1.48%**. This is expected from baseline un-tuned tree models due to sparser training samples below 80% SOH (only ~1.5% of total dataset rows).
- Mean validation residual ($y - \hat{y}$) is $+0.0372\%$, with standard deviation $0.6795\%$, demonstrating virtually zero overall calibration bias.

---

## 12. Selected RUL Model Deep Dive (`rul_hist_gradient_boosting`)

### 12.1 Error Breakdown Across Lifecycle Stages (Validation Set)
Validation cycles were segmented into early-life, mid-life, and near-end-of-life regimes:

| Lifecycle Stage | Sample Count | Percentage | Actual Mean RUL | Pred Mean RUL | MAE (cyc) | RMSE (cyc) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Early-Life ($\mathrm{RUL} \ge 800$)** | 2,707 | 16.3% | 1111.16 | 717.57 | **418.17** | **563.11** |
| **Mid-Life ($300 \le \mathrm{RUL} < 800$)** | 7,599 | 45.8% | 513.82 | 524.20 | **101.83** | **133.30** |
| **Near-End-of-Life ($\mathrm{RUL} < 300$)** | 6,300 | 38.0% | 149.50 | 172.83 | **42.78** | **66.15** |

### 12.2 Longevity Cohort Heterogeneity (Validation Set)
Batteries in the dataset exhibit widely divergent lifespans (ranging from ~300 cycles to over 2,200 cycles). Analyzing performance across battery longevity cohorts reveals key model behavior:

| Longevity Cohort | Batteries in Val | Total Cycles | Actual Cohort Mean Life | MAE (cyc) | RMSE (cyc) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **High-Cycle ($\ge 1000$ cycles)** | 6 | 7,272 | 1,212 cycles | **209.78** | **358.48** |
| **Mid-Cycle (500 – 999 cycles)** | 7 | 5,576 | 796 cycles | **75.30** | **103.48** |
| **Low-Cycle ($< 500$ cycles)** | 8 | 3,758 | 470 cycles | **61.18** | **84.33** |

### 12.3 RUL Error Insights & Physical Interpretation
- **Near-EOL Precision**: For operational decision-making, accuracy near retirement is critical. For cycles where $\mathrm{RUL} < 300$, the model attains an MAE of **42.78 cycles** (RMSE 66.15 cycles).
- **Early-Life Underestimation**: For early-life cycles ($\mathrm{RUL} \ge 800$), the model under-predicts total lifespan (mean actual 1111 vs pred 717). This occurs because during early cycles, degradation signals ($Q_{\mathrm{charge}}$, $\mathrm{IR}$) have not yet differentiated long-lived cells from short-lived cells.
- **Longevity Discrepancy**: Low-cycle batteries achieve high accuracy (MAE 61 cycles), whereas high-cycle batteries (specifically battery 132, which survived 1,934 cycles) encounter higher error (cohort MAE 209 cycles) because the tree averages early cycles toward the global dataset mean.

---

## 13. Battery-Level Heterogeneity Analysis

Because training and evaluation are partitioned strictly by `battery_id`, evaluating cross-battery performance variance is vital to test whether the models generalize across individual physical cells.

### 13.1 SOH Performance Distribution Across Validation & Test Batteries
- **Validation Partition (21 Batteries)**:
  - Median Battery MAE: **0.4086%**
  - Best Generalization: Battery 137 (MAE **0.1458%**, RMSE 0.2138%, $R^2 = 0.9970$), Battery 42 (MAE **0.1553%**).
  - Worst Generalization: Battery 58 (MAE **1.2541%**, RMSE 1.5423%), Battery 62 (MAE **1.0739%**).
  - Note: Even on the worst-performing validation battery (58), the model captures 94.1% of variance ($R^2 = 0.9411$).
- **Test Partition (21 Batteries)**:
  - Median Battery MAE: **0.2985%**
  - Best Generalization: Battery 139 (MAE **0.1584%**, RMSE 0.2074%, $R^2 = 0.9976$), Battery 24 (MAE **0.1618%**).
  - Worst Generalization: Battery 88 (MAE **1.4636%**, RMSE 2.1928%, $R^2 = 0.8860$).

### 13.2 RUL Performance Distribution Across Validation & Test Batteries
- **Validation Partition (21 Batteries)**:
  - 18 out of 21 batteries exhibit strong tracking with $R^2 > 0.50$ (10 batteries achieve $R^2 > 0.80$).
  - Best Generalization: Battery 58 (MAE **25.56 cycles**, RMSE 32.98), Battery 33 (MAE **25.60 cycles**, RMSE 34.88, $R^2 = 0.9725$), Battery 120 (MAE **26.53 cycles**, $R^2 = 0.9881$).
  - Outlier Battery: Battery 132 (1,934 cycles) exhibited MAE of **564.77 cycles**. Because battery 132 has more than double the lifespan of the typical cell, the baseline tree predicts early cycles closer to 800–1000 cycles until visible degradation appears after cycle 1000.
- **Test Partition (21 Batteries)**:
  - 14 out of 21 batteries achieve $R^2 > 0.65$ (9 batteries achieve $R^2 > 0.80$).
  - Best Generalization: Battery 30 (MAE **32.05 cycles**, RMSE 38.32, $R^2 = 0.9789$), Battery 139 (MAE **34.52 cycles**, RMSE 45.83, $R^2 = 0.9922$).
  - Outlier Battery: Battery 104 (1,077 cycles) exhibited MAE of **391.35 cycles**.

---

## 14. Feature Importance Analysis

Feature importances were computed using scikit-learn's model-derived `permutation_importance` on the validation partition (5 repeats, random seed 42) for the selected `HistGradientBoostingRegressor` models.

### 14.1 Top Features for SOH Prediction
| Rank | Feature | Permutation Importance | Physical Rationale & Domain Insight |
| :---: | :--- | :---: | :--- |
| **1** | `QCharge` | **0.7377** | Charge capacity directly correlates with reversible lithium inventory. As active material degrades, $Q_{\mathrm{charge}}$ drops in tandem with discharge capacity. |
| **2** | `QCharge_lag1` | **0.1688** | Previous-cycle charge capacity provides temporal continuity and smooths single-cycle measurement noise. |
| **3** | `cycle` | **0.0421** | Cumulative cycle count provides monotonic degradation progression. |
| **4** | `chargetime_lag1` | **0.0141** | Historical duration of constant-current / constant-voltage charging phase reflects cell impedance growth. |
| **5** | `chargetime` | **0.0139** | Current charging time captures kinetic polarization and rate limitations. |
| **6** | `IR_lag1` | **0.0037** | Internal resistance lag captures electrolyte degradation and SEI growth. |
| **7** | `IR_is_zero` | **0.0030** | Indicator separating genuine zero impedance readings from sensor artifacts. |
| **8** | `Tmin` | **0.0030** | Baseline thermal operating envelope. |
| **9** | `Tmax` | **0.0024** | Peak exothermic self-heating during charging. |
| **10** | `IR` | **0.0022** | Current internal resistance. |

### 14.2 Top Features for RUL Prediction
| Rank | Feature | Permutation Importance | Physical Rationale & Domain Insight |
| :---: | :--- | :---: | :--- |
| **1** | `QCharge` | **0.2751** | Primary thermodynamic health indicator; lower charge intake signals closeness to end-of-life. |
| **2** | `cycle` | **0.1443** | Primary temporal baseline; RUL definitionally decreases as cycle index advances. |
| **3** | `chargetime` | **0.0809** | Charging kinetics; shortening charging phases correlate strongly with late-life degradation. |
| **4** | `chargetime_lag1` | **0.0486** | Temporal smoothing of charge kinetics. |
| **5** | `IR` | **0.0457** | Internal resistance growth directly accelerates battery end-of-life voltage cutoff triggers. |
| **6** | `QCharge_lag1` | **0.0423** | Lagged charge capacity reference. |
| **7** | `Tavg` | **0.0376** | Operating temperature regime influencing degradation acceleration rates. |
| **8** | `IR_lag1` | **0.0297** | Prior-cycle resistance state. |
| **9** | `QCharge_delta` | **0.0158** | Velocity of capacity degradation ($\Delta Q$). Accelerating capacity loss indicates impending cell failure. |
| **10** | `Tavg_lag1` | **0.0140** | Prior-cycle temperature baseline. |

### 14.3 Domain Interpretation Summary
The empirical feature importance alignments fully corroborate electrochemical principles:
- **SOH** is overwhelmingly governed by thermodynamic charge acceptance (`QCharge` + `QCharge_lag1` account for **90.6%** of importance).
- **RUL** is governed by a balanced combination of current degradation state (`QCharge`), elapsed exposure (`cycle`), kinetic charging rates (`chargetime`), and internal cell resistance (`IR`), with rate-of-change features (`QCharge_delta`) playing an active role.

---

## 15. Diagnostic Visualizations & Figure Catalog

Six diagnostic visualization plots have been generated and saved under `reports/modeling/task_2l/figures/`:

1. **SOH Actual vs. Predicted Scatter (Val & Test)**:  
   `reports/modeling/task_2l/figures/soh_actual_vs_predicted.png`  
   *Displays tight clustering along the identity line ($y=x$) across both Validation and Test sets, demonstrating strong generalization without saturation.*
2. **SOH Residual Distribution**:  
   `reports/modeling/task_2l/figures/soh_residual_distribution.png`  
   *Displays near-perfect Gaussian zero-centered error distribution ($\mu = 0.04\%$) with narrow standard deviation.*
3. **SOH Feature Importance**:  
   `reports/modeling/task_2l/figures/soh_feature_importance.png`  
   *Horizontal bar chart showing the overwhelming dominance of $Q_{\mathrm{charge}}$ and $Q_{\mathrm{charge}, t-1}$ in driving SOH prediction.*
4. **RUL Actual vs. Predicted Scatter (Val & Test)**:  
   `reports/modeling/task_2l/figures/rul_actual_vs_predicted.png`  
   *Shows tight tracking along the identity line for cycles $< 800$, and captures the transition to conservative predictions in early-life high-cycle regimes.*
5. **RUL Residual Distribution**:  
   `reports/modeling/task_2l/figures/rul_residual_distribution.png`  
   *Displays the residual distribution centered near zero with slight right-skew driven by high-cycle early-life battery underestimations.*
6. **RUL Feature Importance**:  
   `reports/modeling/task_2l/figures/rul_feature_importance.png`  
   *Highlights the balanced contributions of $Q_{\mathrm{charge}}$, `cycle`, `chargetime`, and `IR`.*

---

## 16. Limitations of Baselines & Next Steps for Task 2M

While the Task 2L baselines establish strong benchmarks, several key architectural limitations were identified:

1. **Early-Cycle RUL Inaccuracy on High-Cycle Batteries**:
   - Because early-cycle feature signatures are nearly identical between batteries that eventually fail at 600 cycles versus 1,800 cycles, standard decision trees predict the conditional dataset average (~700–800 cycles).
   - *Task 2M Improvement*: Develop early-life trajectory features (e.g., initial 100-cycle degradation slope, curvature $\Delta^2 Q$, differential capacity peak shifts).
2. **Lack of Hyperparameter Tuning**:
   - Baseline models used standard default parameters (`max_iter=100`, `min_samples_leaf=20`, `learning_rate=0.1`).
   - *Task 2M Improvement*: Systematic Bayesian/Grid optimization of tree depth, leaf regularization, learning rates, and monotonic constraints (`monotonic_cst` to enforce that RUL decreases with cycle index).
3. **Advanced Model Architectures**:
   - In Task 2M, evaluate dedicated gradient boosting frameworks (**XGBoost**, **LightGBM**, **CatBoost**) with sample weighting and specialized loss functions (Huber, Tweedie).
4. **Boundary Condition Enforcement**:
   - Native HistGradientBoosting produced 49 slightly negative RUL predictions on validation (min -49 cycles).
   - *Task 2M Improvement*: Enforce strictly non-negative RUL via log-transformations, rectified activations, or post-prediction physics-informed projection layers.

---

## 17. Reproducibility & Artifact Inventory

All training runs were executed with fixed seed `random_state=42`. All model weights, scalers, metric tables, and plots have been serialized:

### 17.1 Serialized Model Artifacts
Directory: `artifacts/models/task_2l/`
- `soh_dummy.joblib` (863 bytes)
- `soh_ridge.joblib` (1.8 KB — contains fitted `RobustScaler` + `Ridge`)
- `soh_random_forest.joblib` (69.5 MB)
- `soh_hist_gradient_boosting.joblib` (396 KB)
- `rul_dummy.joblib` (863 bytes)
- `rul_ridge.joblib` (1.8 KB — contains fitted `RobustScaler` + `Ridge`)
- `rul_random_forest.joblib` (85.5 MB)
- `rul_hist_gradient_boosting.joblib` (396 KB)

### 17.2 Metrics & Summary Artifacts
Directory: `reports/modeling/task_2l/`
- `task_2l_model_comparison.csv` (High-level model comparison on Val & Test)
- `task_2l_soh_metrics.csv` (Complete SOH metrics across Train, Val, Test)
- `task_2l_rul_metrics.csv` (Complete RUL metrics across Train, Val, Test)
- `task_2l_battery_level_soh.csv` (Per-battery metrics across all 42 Val and Test batteries)
- `task_2l_battery_level_rul.csv` (Per-battery metrics across all 42 Val and Test batteries)
- `task_2l_soh_feature_importance.csv` (Permutation importances for SOH)
- `task_2l_rul_feature_importance.csv` (Permutation importances for RUL)
- `task_2l_summary.json` (Structured machine-readable summary and validation check status)

---


### 17.3 Prediction Artifacts
- 	ask_2l_soh_val_predictions.csv (16,606 rows: battery_id, cycle, actual_soh, pred_dummy, pred_ridge, pred_random_forest, pred_hist_gradient_boosting)
- 	ask_2l_rul_val_predictions.csv (16,606 rows: battery_id, cycle, actual_rul, pred_dummy, pred_ridge, pred_random_forest, pred_hist_gradient_boosting)
- 	ask_2l_soh_test_predictions.csv (18,512 rows)
- 	ask_2l_rul_test_predictions.csv (18,512 rows)
- 	ask_2l_model_parameters.json (Complete scikit-learn hyperparameters for all 8 models)

## 18. Formal Validation Checklist

| Check ID | Verification Condition | Verification Method | Status | Result |
| :---: | :--- | :--- | :---: | :---: |
| **Check 1** | Raw dataset SHA-256 hash unchanged | Read-only SHA-256 computation on `master_dataset.csv` | **PASS** | `0affa1f...` |
| **Check 2** | Raw dataset row count exactly 116,663 | Direct line / row enumeration | **PASS** | 116,663 |
| **Check 3** | Raw dataset column count exactly 11 | Header verification | **PASS** | 11 |
| **Check 4** | Raw dataset completely unmodified | Timestamp and byte-level check | **PASS** | True |
| **Check 5** | Zero NaNs / Infs in processed input matrices | Programmatic scan of Train, Val, Test $X$ | **PASS** | 0 NaNs, 0 Infs |
| **Check 6** | Battery partitions strictly disjoint | Set intersection $\mathrm{Train} \cap \mathrm{Val} \cap \mathrm{Test}$ | **PASS** | Zero overlap |
| **Check 7** | Zero forbidden features in $X$ | Inspection of all 17 feature column names | **PASS** | Zero leaks |
| **Check 8** | All 8 model artifacts loadable from disk | `joblib.load()` on all 8 `.joblib` files | **PASS** | All loadable |
| **Check 9** | Predictions contain zero NaNs or Infs | Programmatic scan of all predicted arrays | **PASS** | Clean predictions |
| **Check 10** | Metrics 100% reproducible upon reload | Reload model artifacts and re-evaluate `val_X` | **PASS** | Bit-exact match |
| **Check 11** | Test set never used for model selection | Selection logic strictly queried `val_RMSE` | **PASS** | Test strictly held out |
| **Check 12** | Task 2K processed artifacts unmodified | Verification of Task 2K row counts and schema | **PASS** | Intact |

---

## 19. Final Verification Verdict

```
==================================================
TASK 2L VERDICT: PASS
==================================================
All 8 baseline models successfully trained and evaluated.
Validation RMSE selection rule rigorously applied.
Zero data leakage detected.
All 12 programmatic validation checks PASSED.
Pipeline is locked and ready for Task 2M (Advanced ML Training).
==================================================
```