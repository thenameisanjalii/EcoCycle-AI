# EcoCycle AI — Physical Plausibility & Data Integrity Audit Report

**Dataset**: `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`  
**Audit Mode**: Read-Only  
**Total Records**: 116,663  
**Total Batteries**: 139  

---

## 1. Investigation 1 — Temperature Plausibility & Internal Bounds

### Observations:
- **`Tavg < 0`**: 8 records (all in Battery 85, cycles 24, 25, 48, 49, 63, 64, 84, 85).
- **`Tmin < 0` / `Tmin = -270.0`**: Exactly 99 records (100% concentrated in Battery 85, all 99 cycles).
- **`Tmax = 400.0`**: Exactly 99 records (100% concentrated in Battery 85, all 99 cycles).
- **Mathematical Consistency (`Tmin <= Tavg <= Tmax`)**:
  - Across all 116,663 records, **0 records violate** `Tmin <= Tavg <= Tmax`.
  - In Battery 85, `-270.0 <= Tavg <= 400.0` mathematically holds, but physically `-270.0 °C` approaches absolute zero (3 K) and `400.0 °C` is extreme furnace heat.
- **Affected Battery**: **Battery `85` only** (all 99 cycles).

---

## 2. Investigation 2 — Internal Resistance (`IR == 0`)

### Observations:
- **Count & Percentage**: 4,922 records (4.22% of dataset).
- **Affected Batteries**: 23 batteries.
- **Distribution Pattern**:
  - **Systemic (Full Lifecycles)**: 7 batteries (`87, 88, 89, 90, 91, 92, 93`) account for **4,903 of the 4,922 zero values (99.6%)**. For these batteries, the IR measurement channel was unrecorded / zero throughout their entire lifespan.
  - **Isolated (Single Cycles)**: 16 batteries (`1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 17, 21, 22, 24, 41`) contain 1 or 2 isolated zero records (typically around cycle 12-13 or cycle 850-900).
- **Other Variables**: In these 4,922 records, all other telemetry variables (`QCharge`, `QDischarge`, `SOH`, `Tavg`) exhibit normal expected distributions (e.g. mean SOH: 96.53%, mean QDischarge: 1.040 Ah).

---

## 3. Investigation 3 — Charge Time (`chargetime`)

### Observations:
- **Summary**:
  - Median: 10.31 minutes.
  - Q1: 10.04 minutes | Q3: 11.18 minutes.
  - Maximum: 3,934.71 minutes (~65.58 hours).
- **Extreme Records (`chargetime > 60` min)**: Exactly **17 records** (0.015% of dataset).
  - 11 records cluster around **~3,932 to 3,935 minutes** (~65.5 hours / ~2.7 days).
  - 3 records cluster around **~419 minutes** (~7.0 hours).
  - 3 records cluster around **~278 to 281 minutes** (~4.6 hours).
- **Top 20 Largest Charge Time Records**:

| Battery ID | Cycle | Charge Time (min) | QCharge (Ah) | QDischarge (Ah) | Tavg (°C) | Tmax (°C) | Tmin (°C) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `61` | 50.0 | 3934.71 | 0.9283 | 1.0715 | 32.17 | 34.92 | 30.20 |
| `81` | 77.0 | 3934.12 | 0.9108 | 1.0597 | 36.12 | 38.48 | 30.85 |
| `93` | 48.0 | 3933.84 | 0.9458 | 1.0956 | 30.55 | 31.54 | 29.38 |
| `75` | 49.0 | 3933.74 | 0.9429 | 1.0878 | 31.85 | 34.88 | 30.00 |
| `88` | 51.0 | 3933.62 | 0.9735 | 1.1007 | 29.60 | 30.89 | 28.85 |
| `79` | 71.0 | 3933.46 | 0.9390 | 1.0792 | 31.82 | 33.53 | 30.14 |
| `77` | 52.0 | 3933.40 | 0.9903 | 1.0830 | 33.16 | 37.10 | 30.17 |
| `73` | 51.0 | 3933.12 | 1.0108 | 1.0964 | 33.55 | 37.58 | 30.25 |
| `87` | 49.0 | 3932.94 | 0.9765 | 1.0790 | 32.20 | 36.39 | 29.90 |
| `67` | 50.0 | 3932.59 | 0.9940 | 1.0934 | 33.13 | 36.49 | 31.58 |
| `91` | 70.0 | 3932.51 | 0.9766 | 1.0919 | 33.87 | 36.75 | 30.37 |
| `16` | 13.0 | 419.87 | 1.0655 | 1.0620 | 32.28 | 36.74 | 29.44 |
| `15` | 13.0 | 419.79 | 1.0741 | 1.0708 | 32.35 | 36.48 | 29.77 |
| `6` | 13.0 | 418.82 | 1.0790 | 1.0752 | 30.77 | 32.96 | 29.26 |
| `42` | 887.0 | 280.98 | 0.8934 | 0.9891 | 33.55 | 38.58 | 29.47 |
| `25` | 902.0 | 278.98 | 0.9020 | 0.9596 | 33.81 | 38.50 | 29.46 |
| `4` | 879.0 | 278.28 | 0.9368 | 1.0456 | 30.12 | 31.32 | 29.34 |
| `72` | 508.0 | 41.64 | 0.8805 | 0.8392 | 32.65 | 35.77 | 30.80 |
| `89` | 494.0 | 40.98 | 0.8809 | 0.8338 | 32.02 | 37.30 | 29.47 |
| `77` | 425.0 | 40.78 | 0.8843 | 0.8402 | 33.28 | 39.99 | 30.15 |

- **Concentration**: These extreme charge times are **isolated single cycles** within individual battery lifecycles (e.g. cycle 50 in Battery 61, cycle 77 in Battery 81), representing scheduled laboratory pauses, rest phases, or characterization rests.

---

## 4. Investigation 4 — State of Health (`SOH > 100`)

### Observations:
- **Count & Percentage**: 10,784 records (9.24% of dataset).
- **Maximum SOH**: 104.79%.
- **Affected Batteries**: **All 139 batteries**.
- **Cycle Distribution**:
  - Min Cycle: 1.0 | Q1 Cycle: 32.0 | Median Cycle: 58.0 | Q3 Cycle: 122.0 | Max Cycle: 598.0.
  - SOH > 100 occurs exclusively during the **initial operational phase** of each battery's lifecycle.
  - Physical Plausibility: Brand new lithium-ion cells deliver initial capacity exceeding nominal/nameplate capacity before stabilization and progressive degradation.

---

## 5. Investigation 5 — RUL Consistency

### Observations:
- **Formula Verification**:
  $$\text{RUL} = \text{max\_cycle\_for\_that\_battery} - \text{cycle}$$
  Verified across **all 116,663 records**: **100.0% exact match** (Max absolute difference = 0.0).
- **Terminal Cycle Check**: Every battery has exactly **one** record where `RUL = 0` (its final recorded cycle).
- **Monotonicity**: RUL decreases strictly monotonically as cycle increases across all 139 batteries (0 violations).
- **Negative Values**: Exactly **0** negative RUL values.

---

## 6. Investigation 6 — QCharge vs QDischarge Relationship

### Observations:
- **Ranges**:
  - `QCharge`: Min = 0.8289 Ah, Max = 1.9679 Ah.
  - `QDischarge`: Min = 0.8250 Ah, Max = 1.1214 Ah.
  - Zero / Negative Values: **0** in both columns.
- **Coulombic Consistency**:
  - Across 99.97% of records, $|\text{QCharge} - \text{QDischarge}| < 0.1$ Ah (mean difference: -0.0002 Ah).
- **Linear Drift in Battery 19**:
  - Exactly **28 records** have `QCharge > 1.2` Ah.
  - All 28 occur in **Battery 19 between cycles 12.0 and 39.0**, where QCharge steps upward by ~0.0275 Ah/cycle from 1.225 to 1.968 Ah, while QDischarge remains stable (~1.070 Ah).
  - At cycle 41 (following a 1-cycle gap at cycle 40), QCharge resets back to normal (1.069 Ah).

---

## 7. Investigation 7 — Cross-Variable Co-occurrence

### Observations:
- **Total records with at least one unusual trait**: 15,662 records (13.43% of dataset).
- **Records with multiple flags**: Only 105 records (0.09% of dataset).
  - Co-occurrence of `chargetime > 100` and `QCharge > 1.2`: 0.
  - Co-occurrence of Temperature anomaly and `IR == 0`: 0 (Battery 85 has normal IR).
  - Co-occurrence of Temperature anomaly and `chargetime > 100`: 0.
- **Conclusion**: The identified physical/statistical traits occur **independently** in distinct functional subsystems (e.g. sensor hardware, battery initial capacity, laboratory rest pauses).

---

## 8. Final Classification of Findings

| Finding / Variable | Observation Type | Classification | Actionable Audit Guidance |
| :--- | :--- | :--- | :--- |
| **Temperature Bounds** (`Tmin <= Tavg <= Tmax`) | Relationship | **Internally Consistent** | Confirmed 100% consistent across all 116,663 records. |
| **Battery 85 Temperatures** (`-270` / `400` / `Tavg < 0`) | Physical Telemetry | **Physically Suspicious / Requires source documentation** | Likely sensor channel failure/sentinel. |
| **IR == 0** (4,922 records) | Sensor Measurement | **Physically Suspicious / Requires source documentation** | Unlogged IR sensor for 7 batteries; isolated in 16. |
| **Charge Time Spikes** (17 records > 60 min) | Protocol / Resting | **Statistically Unusual / Potentially Valid Resting Pause** | Consistent with multi-day resting protocols. |
| **SOH > 100** (10,784 records) | Capacity Target | **Potentially Valid / Structurally Consistent** | Initial fresh-cell capacity exceeding nominal rating. |
| **RUL Formula** (`max_cycle - cycle`) | Life Ground Truth | **Internally Consistent (Confirmed Exact)** | Ground truth deterministic lifecycle formula. |
| **QCharge Drift** (Battery 19, cycles 12-39) | Amp-Hour Integration | **Statistically Unusual / Requires source documentation** | Cycler coulometer drift prior to cycle 40 reset. |
