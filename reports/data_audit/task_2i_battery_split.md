# EcoCycle AI — Task 2I Battery-Grouped 70/15/15 Split Audit Report

**Dataset Audited**: `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`  
**Audit Mode**: Strict Read-Only (Raw Dataset Unmodified)  
**Partitioning Method**: Reproducible Battery-Grouped Split (Leave-Batteries-Out)  
**Random Seed**: `42`  

---

## 1. Executive Summary & Splitting Design
To eliminate temporal and identifier leakage established in Task 2G & 2H, a strictly battery-grouped 70/15/15 train/validation/test split was implemented. Every individual cycle record belonging to a given battery is assigned **exclusively** to one single partition:
- **Total Batteries**: `139`
- **Total Records**: `116,663`
- **Zero Inter-Partition Overlap**: No battery appears in more than one partition.
- **Zero Data Loss / Double Counting**: Exactly 116,663 rows accounted for.
- **No Transformations / No Modeling**: No scalers, imputers, encoders, feature engineering, or ML models have been fitted.

---

## 2. Partition Allocations & Verification

| Partition | Target Ratio | Battery Count | Battery % | Row Count | Row % | Overlap Violations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 70% | **97** | 69.78% | **81,545** | 69.90% | **0** |
| **Validation** | 15% | **21** | 15.11% | **16,606** | 14.23% | **0** |
| **Test** | 15% | **21** | 15.11% | **18,512** | 15.87% | **0** |
| **Total** | 100% | **139** | 100.00% | **116,663** | 100.00% | **0** |

---

## 3. Strict Overlap & Integrity Verification
- **Pairwise Intersection Tests**:
  - `Train ∩ Validation`: **$\emptyset$ (0 batteries)** — **PASSED**
  - `Train ∩ Test`: **$\emptyset$ (0 batteries)** — **PASSED**
  - `Validation ∩ Test`: **$\emptyset$ (0 batteries)** — **PASSED**
- **Completeness Test**:
  - Total unique batteries assigned: **139 / 139 (100.0%)** — **PASSED**
  - Unassigned batteries: **0** — **PASSED**
- **Row Accounting Test**:
  - $81,545 + 16,606 + 18,512 = 116,663$ records (exact match with raw file) — **PASSED**

---

## 4. Exact Battery ID Assignments

### A. Training Batteries (97 Batteries):
`[1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 23, 25, 26, 27, 28, 29, 31, 32, 34, 35, 36, 37, 39, 40, 41, 43, 44, 45, 46, 47, 48, 50, 51, 52, 54, 55, 56, 57, 61, 63, 65, 66, 67, 68, 69, 70, 71, 73, 74, 77, 78, 79, 81, 82, 83, 84, 85, 86, 87, 90, 94, 95, 96, 97, 98, 101, 102, 105, 106, 109, 110, 111, 112, 113, 114, 116, 118, 119, 121, 123, 125, 126, 127, 128, 129, 131, 133, 135, 136, 138]`

### B. Validation Batteries (21 Batteries):
`[33, 38, 42, 49, 58, 59, 60, 62, 64, 76, 80, 89, 91, 92, 99, 115, 120, 124, 132, 134, 137]`

### C. Test Batteries (21 Batteries):
`[2, 3, 15, 21, 22, 24, 30, 53, 72, 75, 88, 93, 100, 103, 104, 107, 108, 117, 122, 130, 139]`

*(Full per-battery records are archived in [`reports/data_audit/task_2i_split_assignments.csv`](file:///C:/Users/patid/.gemini/antigravity/scratch/EcoCycle-AI/reports/data_audit/task_2i_split_assignments.csv))*

---

## 5. Target & Feature Distribution Comparison Across Partitions

| Feature / Target | Partition | Mean | Std Dev | Q1 (25%) | Median (50%) | Q3 (75%) | Min | Max |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`SOH` (%)** | All Data | 96.4072 | 4.5205 | 95.2676 | 98.0745 | 99.5077 | 74.5527 | 104.7925 |
| | **Train** | 96.4608 | 4.4481 | 95.3414 | 98.1021 | 99.5165 | 74.5527 | 104.7925 |
| | **Validation** | 96.2140 | 5.0433 | 94.8879 | 98.1828 | 99.5768 | 74.8398 | 102.5077 |
| | **Test** | 96.3445 | 4.3317 | 95.2281 | 97.8652 | 99.3789 | 75.3283 | 101.9961 |
| **`RUL` (cycles)** | All Data | 496.6931 | 373.6661 | 211.0000 | 425.0000 | 704.0000 | 0.0000 | 2236.0000 |
| | **Train** | 489.5007 | 356.3972 | 210.0000 | 429.0000 | 694.0000 | 0.0000 | 1851.0000 |
| | **Validation** | 472.9779 | 367.1808 | 196.0000 | 395.0000 | 674.0000 | 0.0000 | 1581.0000 |
| | **Test** | 549.6492 | 442.6649 | 231.0000 | 442.0000 | 788.0000 | 0.0000 | 2236.0000 |
| **`cycle`** | All Data | 498.0547 | 373.6113 | 212.0000 | 427.0000 | 706.0000 | 1.0000 | 2237.0000 |
| | **Train** | 490.9116 | 356.3332 | 211.0000 | 430.0000 | 696.0000 | 1.0000 | 1852.0000 |
| | **Validation** | 474.1239 | 367.1607 | 197.0000 | 396.0000 | 675.0000 | 1.0000 | 1582.0000 |
| | **Test** | 550.9866 | 442.6114 | 232.0000 | 443.0000 | 790.0000 | 1.0000 | 2237.0000 |
| **`QDischarge` (Ah)** | All Data | 1.0391 | 0.0505 | 1.0226 | 1.0531 | 1.0716 | 0.8250 | 1.1214 |
| | **Train** | 1.0395 | 0.0496 | 1.0232 | 1.0534 | 1.0718 | 0.8250 | 1.1214 |
| | **Validation** | 1.0395 | 0.0566 | 1.0210 | 1.0547 | 1.0745 | 0.8282 | 1.1171 |
| | **Test** | 1.0368 | 0.0490 | 1.0217 | 1.0509 | 1.0682 | 0.8306 | 1.1077 |
| **`QCharge` (Ah)** | All Data | 1.0389 | 0.0492 | 1.0225 | 1.0523 | 1.0702 | 0.8289 | 1.9679 |
| | **Train** | 1.0397 | 0.0491 | 1.0231 | 1.0527 | 1.0704 | 0.8289 | 1.9679 |
| | **Validation** | 1.0369 | 0.0507 | 1.0205 | 1.0525 | 1.0722 | 0.8322 | 1.1166 |
| | **Test** | 1.0370 | 0.0480 | 1.0215 | 1.0505 | 1.0673 | 0.8347 | 1.1189 |
| **`IR` (Ω)** | All Data | 0.0157 | 0.0036 | 0.0154 | 0.0161 | 0.0170 | 0.0000 | 0.0226 |
| | **Train** | 0.0162 | 0.0027 | 0.0155 | 0.0163 | 0.0171 | 0.0000 | 0.0226 |
| | **Validation** | 0.0139 | 0.0058 | 0.0150 | 0.0159 | 0.0167 | 0.0000 | 0.0214 |
| | **Test** | 0.0152 | 0.0038 | 0.0151 | 0.0157 | 0.0167 | 0.0000 | 0.0217 |
| **`Tavg` (°C)** | All Data | 34.3558 | 2.0092 | 33.0716 | 34.1618 | 35.7189 | -8.6572 | 73.5538 |
| | **Train** | 34.4826 | 2.0343 | 33.2045 | 34.2925 | 35.8459 | -8.6572 | 73.5538 |
| | **Validation** | 34.3739 | 1.8827 | 33.2796 | 33.8906 | 35.7369 | 28.9196 | 38.6473 |
| | **Test** | 33.7813 | 1.9053 | 32.4939 | 33.7591 | 34.9827 | 28.5303 | 38.4116 |

### Distribution Observations:
1. **SOH Uniformity**: Mean SOH is remarkably consistent across partitions (Train: 96.46%, Val: 96.21%, Test: 96.34%), ensuring balanced degradation distributions.
2. **Discharge & Charge Capacities**: `QDischarge` and `QCharge` medians and means align within < 0.003 Ah across all three partitions.
3. **Anomalous Batteries Distribution**:
   - Battery 85 (temperature fault): Assigned to **Train** (enables algorithms to encounter and learn to handle extreme telemetry).
   - Batteries 87–93 (unmeasured zero IR): Partitioned across **Train (87, 90)**, **Validation (89, 91, 92)**, and **Test (88, 93)**, ensuring the validation and test sets evaluate out-of-sample robustness on both normal and unmeasured IR cells.

---

## 6. Reproducibility Specification
The partition split can be deterministically reproduced using the following code:

```python
import numpy as np
import pandas as pd

# Load master dataset
df = pd.read_csv("master_dataset.csv")
unique_batteries = sorted(df['battery_id'].unique().tolist())

# Fixed Seed
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
shuffled = np.random.permutation(unique_batteries)

train_batteries = sorted(shuffled[:97].tolist())
val_batteries = sorted(shuffled[97:118].tolist())
test_batteries = sorted(shuffled[118:].tolist())
```

---

## 7. Mandatory Policy Confirmations
1. **Grouping Identifier Only**: `battery_id` is certified as a grouping identifier only. It will never be included as an input feature in any ML matrix $X$.
2. **No Model Fitting**: Zero scalers, imputers, encoders, or machine learning models have been fitted on this split.
3. **No Feature Engineering**: No lag, rolling, or derivative features have been created.
4. **Raw Dataset Integrity**: `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv` was read strictly in read-only mode and remains 100% unaltered.
