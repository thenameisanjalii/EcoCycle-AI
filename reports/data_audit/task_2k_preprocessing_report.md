# EcoCycle AI — Task 2K: Preprocessing Implementation & Causal Feature Engineering Report

**Project:** EcoCycle AI — AI-Driven Battery Health and Second-Life Assessment Platform  
**Target Raw Dataset:** `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv` (Accessed strictly in READ-ONLY mode)  
**Report Location:** `reports/data_audit/task_2k_preprocessing_report.md`  
**Status:** COMPLETE (Formal Implementation & Verification Report)  
**Date:** September 2026  
**Auditor:** ML & Data Engineering Team  

---

## 1. Executive Overview

This report documents the completion of **Task 2K: Preprocessing Implementation and Causal Feature Engineering** for the EcoCycle AI platform. In this phase, all preprocessing policies, mathematical decisions, and causal feature engineering rules locked in Tasks 2G, 2H, 2I, and 2J were formally executed.

### Core Implementation Accomplishments
1. **Raw Data Protection:** The original raw dataset `master_dataset.csv` was accessed strictly in read-only mode and remains 100% untouched and byte-identical (verified via SHA-256 before and after processing).
2. **Locked Battery-Grouped Split (Seed 42):** Exactly partitioned the 139 batteries into **97 Train, 21 Validation, and 21 Test** batteries, ensuring zero cell overlap.
3. **Train-Only Parameter Fitting:** All imputation medians, temperature offsets, and scalers were fitted strictly on the Training partition to prevent any data leakage.
4. **Causal Anomaly Remediation:**
   - Addressed 4,922 `IR == 0.0` records via causal forward-fill for isolated dropouts (19 rows) and train-only median imputation (`0.016321 Ohm`) for systemic missingness (4,903 rows), fully preserving the `IR_is_zero` binary indicator flag.
   - Handled Battery 85 temperature saturation via train-cohort median offset imputation and preserved the `temp_sensor_fault = 1` flag.
   - Handled 24 transient `Tmin == 0.0` dropouts via strictly causal forward-fill ($t-1$).
5. **Causal Feature Engineering:** Engineered 8 strictly backward-looking lag and delta features (`IR_lag1`, `IR_delta`, `QCharge_lag1`, `QCharge_delta`, `Tavg_lag1`, `Tavg_delta`, `chargetime_lag1`, `chargetime_delta`) with neutral zero-delta fallback at cycle 1.
6. **Exported 6 Partitioned Datasets:** Successfully created clean, un-leaked CSV datasets in `data/processed/` for both SOH and RUL modeling.
7. **18 Formal Validation Checks Passed:** Automatically executed and confirmed all 18 validation checks with 100% compliance.

---

## 2. Dataset Splitting & Partition Architecture

The dataset was partitioned according to the locked Task 2I specification:
- **Random Seed:** `42`
- **Battery Universe:** 139 unique batteries (`1` to `139`)
- **Shuffled Split:** `rng = np.random.RandomState(42); shuffled = rng.permutation(unique_batteries)`
- **Partition Allocations:**
  - **Train:** First 97 batteries (69.78% of batteries, **81,545 records**, 69.90% of data)
  - **Validation:** Next 21 batteries (15.11% of batteries, **16,606 records**, 14.23% of data)
  - **Test:** Final 21 batteries (15.11% of batteries, **18,512 records**, 15.87% of data)

### Partition Validation
- **Train $\cap$ Validation:** $\emptyset$ (0 batteries)
- **Train $\cap$ Test:** $\emptyset$ (0 batteries)
- **Validation $\cap$ Test:** $\emptyset$ (0 batteries)
- **Total Batteries Accounted For:** Exactly 139 out of 139
- **Total Rows Accounted For:** $81,545 + 16,606 + 18,512 = \mathbf{116,663}$ (100.00%)

---

## 3. Preprocessing Transformations Performed

All transformations were strictly causal and fitted exclusively on training data:

### A. Zero Internal Resistance (`IR == 0.0`)
- **Flagging:** Generated `IR_is_zero = (IR == 0.0).astype(int)` across all partitions.
  - Exactly **4,922 records** have `IR_is_zero = 1` (1,531 in Train, 2,398 in Val, 993 in Test).
- **Imputation:**
  - In isolated dropout batteries (16 batteries, 19 records), applied **causal forward-fill** ($IR_t = IR_{t-1}$).
  - In systemic unmeasured batteries (Batteries 87–93, 4,903 records) and any remaining NaNs, imputed numerical `IR` using the median of non-zero IR from the Training partition:
    $$IR_{\text{impute}} = \text{Median}(IR_{\text{train}, IR > 0}) = \mathbf{0.0163213845}\text{ }\Omega$$
- **Verification:** After imputation, numerical `IR` contains 0 zeros and 0 NaNs across all 116,663 records, while `IR_is_zero` preserves the exact missingness signature.

### B. Battery 85 Temperature Sensor Saturation
- **Flagging:** Generated `temp_sensor_fault = (battery_id == 85).astype(int)`.
  - Exactly **99 records** have `temp_sensor_fault = 1` (all in Train partition, 0 in Val, 0 in Test).
- **Imputation:**
  - For the 8 cycles in Battery 85 with negative average temperature ($T_{\text{avg}} < 0^\circ\text{C}$), imputed $T_{\text{avg}}$ via causal forward-fill from preceding valid cycles.
  - Imputed $T_{\min}$ and $T_{\max}$ for Battery 85 using median temperature offsets derived strictly from healthy training batteries:
    $$\Delta T_{\min,\text{train}} = \text{Median}(T_{\text{avg}} - T_{\min})_{\text{train, healthy}} = \mathbf{3.049875}^\circ\text{C}$$
    $$\Delta T_{\max,\text{train}} = \text{Median}(T_{\max} - T_{\text{avg}})_{\text{train, healthy}} = \mathbf{3.571058}^\circ\text{C}$$
    $$T_{\min} = T_{\text{avg}} - \Delta T_{\min,\text{train}}, \quad T_{\max} = T_{\text{avg}} + \Delta T_{\max,\text{train}}$$
- **Verification:** $T_{\min} \le T_{\text{avg}} \le T_{\max}$ holds with 0 violations across all 99 cycles of Battery 85.

### C. Transient Sensor Dropouts (`Tmin == 0.0`)
- **Imputation:** Across the 24 records exhibiting digital null dropouts (occurring in Batteries 87–93, cycles $\ge 75$), applied strictly **causal forward-fill**:
  $$T_{\min, t} = T_{\min, t-1}$$
- **Verification:** 0 records with $T_{\min} = 0.0$ remain; all 24 records satisfy $T_{\min} \le T_{\text{avg}} \le T_{\max}$ with 0 NaNs.

---

## 4. What Was Deliberately NOT Changed

1. **Original Raw CSV:** `master_dataset.csv` was accessed strictly in read-only mode and was NOT modified.
2. **SOH > 100% Values:** Exactly **10,784 records** exhibit $\text{SOH} > 100.0\%$ (up to 104.79%). These were **deliberately NOT clipped to 100%**. SOH is defined mathematically relative to each battery's first-50-cycle average capacity ($\text{SOH} = Q / \bar{Q}_{\le 50} \times 100$); fresh-cell electrochemical break-in naturally exceeds the 50-cycle mean. Clipping the ground truth target would artificially distort regression gradients.
3. **Extreme QCharge / chargetime Values:** Battery 19's coulometric integration drift (up to 1.968 Ah) and laboratory resting spikes (`chargetime > 60 min`) were preserved as valid observations. The feature pipeline applies `RobustScaler` (IQR-based) rather than arbitrary hard truncation.
4. **No Row Deletion:** Zero rows were deleted. All 116,663 records were preserved.
5. **No Model Training:** No machine learning or deep learning models were trained.

---

## 5. Causal Feature Engineering

To capture degradation dynamics and rate-of-change kinetics without temporal leakage, 8 causal features were engineered:

| Engineered Feature | Base Signal | Mathematical Formulation | Cycle 1 Fallback | Causal Direction | Physical Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `IR_lag1` | `IR` | $IR_{t-1}$ within battery | $IR_{t}$ | $t-1$ | Baseline impedance state |
| `IR_delta` | `IR` | $IR_t - IR_{\text{lag1}}$ | `0.0` | $t$ vs $t-1$ | Single-cycle impedance growth |
| `QCharge_lag1` | `QCharge` | $Q_{\text{charge}, t-1}$ within battery | $Q_{\text{charge}, t}$ | $t-1$ | Prior cycle charge capacity |
| `QCharge_delta` | `QCharge` | $Q_{\text{charge}, t} - Q_{\text{charge, lag1}}$ | `0.0` | $t$ vs $t-1$ | Single-cycle charge capacity fade rate |
| `Tavg_lag1` | `Tavg` | $T_{\text{avg}, t-1}$ within battery | $T_{\text{avg}, t}$ | $t-1$ | Prior cycle mean thermal state |
| `Tavg_delta` | `Tavg` | $T_{\text{avg}, t} - T_{\text{avg, lag1}}$ | `0.0` | $t$ vs $t-1$ | Thermal rate-of-change |
| `chargetime_lag1` | `chargetime` | $t_{\text{charge}, t-1}$ within battery | $t_{\text{charge}, t}$ | $t-1$ | Prior cycle charge duration |
| `chargetime_delta` | `chargetime` | $t_{\text{charge}, t} - t_{\text{charge, lag1}}$ | `0.0` | $t$ vs $t-1$ | Charge kinetic duration delta |

### Causality Guarantees
- All lag features use `shift(1)` within each battery.
- Zero future cycles ($t+k$), zero backward rolling windows, and zero centering were used.
- At cycle 1, delta is exactly `0.0`, reflecting zero observed prior change.

---

## 6. Features Allowed vs. Excluded

### Primary SOH Model ($M_{SOH}$)
- **Input Features in $X_{SOH}$ (17 features):**
  1. `IR`
  2. `QCharge`
  3. `Tavg`
  4. `Tmax`
  5. `Tmin`
  6. `chargetime`
  7. `cycle`
  8. `IR_is_zero`
  9. `temp_sensor_fault`
  10. `IR_lag1`
  11. `IR_delta`
  12. `QCharge_lag1`
  13. `QCharge_delta`
  14. `Tavg_lag1`
  15. `Tavg_delta`
  16. `chargetime_lag1`
  17. `chargetime_delta`
- **Target Variable ($y_{SOH}$):** `SOH`
- **Strictly Barred from $X_{SOH}$:** `QDischarge` (direct target leakage $r=0.9989$), `battery_id` (memorization leakage), `RUL` (future information).

### Primary RUL Model ($M_{RUL}$)
- **Input Features in $X_{RUL}$ (17 features currently, 18 with Stage 1 $\widehat{\text{SOH}}$):**
  - Same 17 features as SOH model.
  - In production deployment, Stage 1 will provide predicted $\text{SOH}_{\text{pred}}$.
- **Target Variable ($y_{RUL}$):** `RUL`
- **Strictly Barred from $X_{RUL}$:** `QDischarge`, `battery_id`, ground-truth `SOH` (unavailable at intake).

---

## 7. Exported Datasets Specification

All datasets were exported to `data/processed/` with identical row counts to the partitioned raw subsets:

| File Path | Partition | Target Variable | Features Count in $X$ | Row Count | File Size |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `data/processed/train_soh.csv` | Train | `SOH` | 17 | 81,545 | 21.34 MB |
| `data/processed/val_soh.csv` | Validation | `SOH` | 17 | 16,606 | 4.36 MB |
| `data/processed/test_soh.csv` | Test | `SOH` | 17 | 18,512 | 4.86 MB |
| `data/processed/train_rul.csv` | Train | `RUL` | 17 | 81,545 | 20.37 MB |
| `data/processed/val_rul.csv` | Validation | `RUL` | 17 | 16,606 | 4.16 MB |
| `data/processed/test_rul.csv` | Test | `RUL` | 17 | 18,512 | 4.64 MB |

---

## 8. Results of 18 Formal Validation Checks

| # | Validation Requirement | Target Criterion | Actual Measured Result | Status |
| :-: | :--- | :--- | :--- | :-: |
| **1** | Raw dataset initial hash | Match SHA-256 baseline | `0affa1f6084edf7bba9b99736267a14d6fb...` | **PASS** |
| **2** | Raw dataset post hash | Match initial hash | `0affa1f6084edf7bba9b99736267a14d6fb...` | **PASS** |
| **3** | Hashes identical | Exact equality | Exactly equal | **PASS** |
| **4** | Battery partition overlap | Intersection == 0 | 0 overlapping batteries | **PASS** |
| **5** | Battery population accounting | Exactly 139 batteries | 139 batteries (97 Train, 21 Val, 21 Test) | **PASS** |
| **6** | No `battery_id` in $X$ | Absent from model inputs | Barred from all feature matrices | **PASS** |
| **7** | `SOH` absent from $X_{SOH}$ | Target not in inputs | Absent from $X_{SOH}$ | **PASS** |
| **8** | `RUL` absent from all $X$ | Target not in inputs | Absent from $X_{SOH}$ and $X_{RUL}$ | **PASS** |
| **9** | `QDischarge` absent from $X$ | Leakage feature barred | Absent from both feature matrices | **PASS** |
| **10** | Ground-truth SOH not in $X_{RUL}$ | Production cascade rule | Ground-truth SOH completely absent | **PASS** |
| **11** | Train-only fitting | No test/val statistics used | Parameters fitted strictly on Train split | **PASS** |
| **12** | No future cycle leakage | Strictly backward-looking | Strictly shift(1) per battery | **PASS** |
| **13** | No backward-fill used | Causal ffill only | 100% causal forward-fill | **PASS** |
| **14** | Record count preservation | Exactly 116,663 records | Exactly 116,663 rows across splits | **PASS** |
| **15** | $T_{\min} \le T_{\text{avg}} \le T_{\max}$ | 0 violations after preprocessing | **0 violations (100.000% valid)** | **PASS** |
| **16** | `IR_is_zero` accuracy | Matches 4,922 original zeros | Exactly 4,922 records flagged | **PASS** |
| **17** | `temp_sensor_fault` accuracy | Matches 99 records of B85 | Exactly 99 records flagged | **PASS** |
| **18** | $\text{SOH} > 100$ preservation | Matches 10,784 records | Exactly 10,784 records preserved | **PASS** |

---

## 9. Modular Code Implementation

To ensure clean engineering standards and reusability for upcoming tasks, modular code was created under `src/preprocessing/`:
- [`src/preprocessing/split.py`](file:///C:/Users/patid/.gemini/antigravity/scratch/EcoCycle-AI/src/preprocessing/split.py): Contains `get_battery_splits(df, seed=42)`.
- [`src/preprocessing/pipeline.py`](file:///C:/Users/patid/.gemini/antigravity/scratch/EcoCycle-AI/src/preprocessing/pipeline.py): Contains the `CausalBatteryPreprocessor` class implementing `fit()` and `transform()`.

Fitted `RobustScaler` preprocessors were serialized to:
- `artifacts/preprocessors/preprocessor_soh.joblib`
- `artifacts/preprocessors/preprocessor_rul.joblib`

---

## 10. Summary of Unresolved Uncertainties

1. **Hardware Cause for Batteries 87–93 Missing IR:** Provenance records do not specify whether the cycler impedance channel was disabled by technician oversight or channel hardware limitation. However, this uncertainty is fully mitigated by our dual representation: `IR_is_zero` binary indicator flag + training-median imputation.
2. **Hardware Cause for Battery 85 Thermocouple Clamping:** Provenance records do not specify whether the thermocouple detached mechanically or failed electrically. This is fully mitigated by the `temp_sensor_fault` flag + train-offset imputation.

---

## 11. Raw Dataset Safety Certification

> **"master_dataset.csv was accessed strictly in READ-ONLY mode and was NOT modified."**  
> *(Verified: SHA-256 hash `0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88` remains identical before and after processing).*

---
