# EcoCycle AI — Task 2H Modeling Contract

## 1. Executive Summary
This document establishes the formal modeling contract for the **EcoCycle AI** battery intelligence platform. Based on the comprehensive data audit findings from Tasks 2A through 2G, this contract defines the mathematical target definitions, primary deployment feature sets, prohibited leakage paths, splitting policies, and data availability assumptions for predicting:
1. **State of Health (`SOH`)**
2. **Remaining Useful Life (`RUL`)**

No data cleaning, imputation, transformation, feature engineering, dataset splitting, or model training has been performed during this task. This contract serves as the locked architectural blueprint for subsequent engineering phases.

---

## 2. SOH Target Definition
The State of Health target represents the capacity degradation state of a battery relative to its initial stabilized capacity. In accordance with the source synthesis code (`build_master_dataset.py`), the mathematical definition of SOH is:

$$\text{SOH}_t = \frac{QDischarge_t}{\overline{QDischarge}_{\text{cycle} \le 50}} \times 100$$

Where:
- $QDischarge_t$ is the discharge capacity (Ah) measured at cycle $t$.
- $\overline{QDischarge}_{\text{cycle} \le 50}$ is the baseline nominal reference capacity ($C_{\text{ref}}$) established as the arithmetic mean of discharge capacity over the cell's first 50 cycles.
- Target unit: Percentage (%).
- Target range in raw data: Approximately 74.55% to 104.79%.
- Values exceeding 100% in early cycles are mathematically valid consequences of comparing early fluctuating capacity against a 50-cycle average baseline.

---

## 3. RUL Target Definition
The Remaining Useful Life target represents the remaining operational cycle count of a cell before reaching test termination. In accordance with the source synthesis code (`build_master_dataset.py`), the mathematical definition of RUL is:

$$\text{RUL}_t = \max(\text{cycle}) - \text{cycle}_t$$

Where:
- $\max(\text{cycle})$ is the terminal cycle index recorded for that specific battery.
- $\text{cycle}_t$ is the current operating cycle count.
- Target unit: Cycles (integer count).
- Target range in raw data: 0 to 2,236 cycles.
- RUL is an internally consistent, deterministically derived ground-truth label where each cell terminates with exactly one record at $\text{RUL} = 0$.

---

## 4. SOH Feature Contract
Every column in `master_dataset.csv` is classified for SOH estimation:

| Column | Classification | Leakage Risk | Prediction-Time Available | Primary Model | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `IR` | **ALLOWED** | None | Yes (during charge) | **YES** | Physical measurement of internal impedance growth. |
| `QCharge` | **ALLOWED** | None | Yes (end of charge) | **YES** | Delivered charge capacity; non-leaky indicator of capacity retention. |
| `QDischarge` | **FORBIDDEN (Primary) / RESTRICTED (Offline)** | Direct Algebraic Identity / Target Proxy | No (requires full slow discharge test) | **NO** | SOH is mathematically defined as $(QDischarge / C_{\text{ref}}) \times 100$. Ratio is constant per battery. Trivializes ML into a scalar multiplier (~92.8). Unavailable during fast-charge screening. |
| `Tavg` | **ALLOWED** | None | Yes (end of cycle) | **YES** | Average surface temperature reflecting overpotentials and Joule heating. |
| `Tmax` | **ALLOWED** | None | Yes (end of cycle) | **YES** | Peak thermal strain recorded during charging cycle. |
| `Tmin` | **ALLOWED** | None | Yes (end of cycle) | **YES** | Minimum baseline ambient/surface temperature. |
| `chargetime` | **ALLOWED** | None | Yes (end of charge) | **YES** | Charging duration reflecting acceptance kinetics and degradation state. |
| `cycle` | **ALLOWED** | None (with Group split) | Yes (BMS cycle counter) | **YES** | Cumulative operational cycles representing battery age. |
| `battery_id` | **GROUPING/IDENTIFIER ONLY** | Identifier Leakage | Metadata only | **NO** | Categorical identifier causing memorization of cell baseline capacities. |
| `SOH` | **TARGET** | Direct Target Leakage | Target to predict | **NO (Target)** | Ground truth target variable $y_{\text{SOH}}$. |
| `RUL` | **FORBIDDEN** | Temporal / Derived-Target Leakage | No (unknown at inference) | **NO** | Encodes future terminal lifespan $\max(\text{cycle})$. Strictly unknown at inference. |

---

## 5. RUL Feature Contract
Every column in `master_dataset.csv` is classified for RUL estimation:

| Column | Classification | Leakage Risk | Prediction-Time Available | Primary Model | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `IR` | **ALLOWED** | None | Yes (during charge) | **YES** | Impedance growth trajectory accelerates toward the end-of-life knee point. |
| `QCharge` | **ALLOWED** | None | Yes (end of charge) | **YES** | Delivered charge capacity tracks gradual capacity fade over operational life. |
| `QDischarge` | **RESTRICTED (Deployment: Excluded; Research: Allowed)** | None for RUL (Operational Unavailability) | No in fast-charge intake / Yes in full cycle | **NO (Primary Deployment)** | In fast second-life screening, full discharge is not performed to save hours of processing time. Excluded from primary deployment model. |
| `Tavg` | **ALLOWED** | None | Yes (end of cycle) | **YES** | Thermal dissipation telemetry over cycling history. |
| `Tmax` | **ALLOWED** | None | Yes (end of cycle) | **YES** | Maximum thermal stress telemetry. |
| `Tmin` | **ALLOWED** | None | Yes (end of cycle) | **YES** | Minimum thermal baseline telemetry. |
| `chargetime` | **ALLOWED** | None | Yes (end of charge) | **YES** | Charging kinetic duration. |
| `cycle` | **RESTRICTED (Strict Battery-Grouped Only)** | Mathematical Intercept Memorization Risk ($r=-1.0$) | Yes (from BMS) | **YES (with Grouped Split)** | $\text{RUL} = \max(\text{cycle}) - \text{cycle}$. In random row splits, models memorize individual cell lifespans. Must be evaluated strictly on unseen batteries. |
| `battery_id` | **GROUPING/IDENTIFIER ONLY** | Identifier Leakage | Metadata only | **NO** | Causes trees to memorize exact terminal cycle $\max(\text{cycle})$ per battery ID. |
| `SOH` | **RESTRICTED (Ground truth: Forbidden; SOH_pred: Allowed)** | Upstream Ground-Truth Leakage | Estimated via Stage 1 model (SOH_pred) | **YES (as SOH_pred only)** | Ground-truth SOH is derived from early 50-cycle average discharge capacity, which is unknown on an intake battery. Pipeline must consume $\text{SOH}_{\text{pred}}$. |
| `RUL` | **TARGET** | Direct Target Leakage | Target to predict | **NO (Target)** | Ground truth target variable $y_{\text{RUL}}$. |

---

## 6. QDischarge Decision: Primary Deployment vs. Research Benchmarking
The role of `QDischarge` is explicitly resolved across three operational contexts:

1. **For SOH Prediction (FORBIDDEN in Primary Model)**:
   - Within each battery, $\text{SOH} \propto QDischarge$ with zero variance in their ratio ($r = 1.0000$).
   - If included, any machine learning model reduces to learning a single scalar multiplier ($pprox 92.80$). It does not learn battery degradation physics.
   - In operational screening, measuring `QDischarge` requires hours of slow discharge testing. If a technician already performs a full discharge test, capacity is known directly, making ML prediction redundant.

2. **For RUL Prediction — Two Scenarios**:
   - **Scenario A: Research / Offline Benchmark (QDischarge Included)**:
     - In laboratory benchmarks where complete charge and discharge telemetry are available, `QDischarge` does not create direct target leakage for RUL because RUL depends on the future remaining lifespan rather than current static capacity.
   - **Scenario B: Deployment-Oriented Fast Intake Screening (PRIMARY RECOMMENDED MODEL)**:
     - In real-world second-life triage, spent EV packs are plugged in for a quick diagnostic charge (10–20 minutes). Full slow discharge tests are economically and operationally prohibitive at intake.
     - Therefore, **the Primary EcoCycle AI Deployment Model excludes `QDischarge`**, relying strictly on fast-charge diagnostic telemetry (`IR`, `QCharge`, `Tavg`, `Tmax`, `Tmin`, `chargetime`, `cycle`, and upstream `SOH_pred`).

---

## 7. battery_id Policy
- **Policy Statement**: `battery_id` is classified as **GROUPING VARIABLE ONLY**.
- **Enforcement**:
  - `battery_id` must **NEVER** be passed into any feature matrix $X$ for training, validation, or inference.
  - It must **NEVER** be label encoded, one-hot encoded, or target encoded.
  - It is used strictly and exclusively as the grouping key for `GroupKFold`, `GroupShuffleSplit`, and Leave-Batteries-Out cross-validation.

---

## 8. cycle Policy
- **Policy Statement**: `cycle` is **RESTRICTED** and permitted as an ML feature **ONLY under strict Battery-Grouped splitting**.
- **Enforcement**:
  - Because $\text{RUL} = \max(\text{cycle}) - \text{cycle}$, using `cycle` under random row-wise splits allows algorithms to memorize the terminal cycle of each battery, creating artificial $R^2 > 0.99$.
  - Under Battery-Grouped splitting (Leave-Batteries-Out), the model has never observed any cycle of the test battery. The model cannot memorize $\max(\text{cycle})$ and is forced to combine `cycle` with physical state indicators (`IR`, `QCharge`, temperature, $\text{SOH}_{\text{pred}}$) to estimate how much life remains.

---

## 9. SOH_pred Cascaded Architecture Policy
- **Policy Statement**: Ground-truth `SOH` must **NEVER** be fed into the RUL production inference pipeline.
- **Cascaded Architecture**:
  ```
  Raw Charge Telemetry (IR, QCharge, Tavg, Tmax, Tmin, chargetime, cycle)
                              ↓
                  [ Stage 1: SOH Primary Model ]
                              ↓
                        SOH_pred
                              ↓
  Charge Telemetry + SOH_pred + Causal Rolling Slopes
                              ↓
                  [ Stage 2: RUL Primary Model ]
                              ↓
                        RUL_pred
  ```
- **Rationale**: Ground-truth SOH depends on historical early-cycle discharge telemetry that is impossible to know when an uncharacterized battery arrives at a recycling facility. Using `SOH_pred` ensures 100% operational feasibility without leakage.

---

## 10. Final Prediction-Time Feature Sets

### `SOH_PRIMARY` (Fast-Charge Diagnostic Intake):
1. `IR`
2. `QCharge`
3. `Tavg`
4. `Tmax`
5. `Tmin`
6. `chargetime`
7. `cycle`

### `RUL_PRIMARY` (Fast-Charge Diagnostic Intake):
1. `IR`
2. `QCharge`
3. `Tavg`
4. `Tmax`
5. `Tmin`
6. `chargetime`
7. `cycle`
8. `SOH_pred` *(generated via Stage 1 model)*

---

## 11. Leakage Prevention Rules (Implementation Constraints)
Future pipeline implementations must strictly obey the following nine rules:
1. **Rule 1 (Grouping Enforcement)**: Train, validation, and test splits must be partitioned strictly by `battery_id`. Zero cycles of test batteries may appear in training.
2. **Rule 2 (Identifier Exclusion)**: Drop `battery_id` from feature matrices $X$ immediately after split generation.
3. **Rule 3 (Target Isolation)**: `SOH` and `RUL` must never be present in feature matrices $X$.
4. **Rule 4 (No Target Cross-Leakage)**: `RUL` must never be used to predict `SOH`.
5. **Rule 5 (SOH Ground-Truth Exclusion)**: Ground-truth `SOH` must never be passed to the RUL inference pipeline; only `SOH_pred` is permitted.
6. **Rule 6 (QDischarge Exclusion in Primary)**: Primary deployment models must not require `QDischarge`.
7. **Rule 7 (Causal Time-Series Directionality)**: Any engineered rolling or lag features must be strictly causal (backward-looking only: $t, t-1, \dots, t-k$). Future cycles ($t+k$) are strictly prohibited.
8. **Rule 8 (Transformation Isolation)**: All scalers, normalizers, and encoders must be fitted strictly on the Training batteries and applied downstream to Validation and Test batteries.
9. **Rule 9 (No Global Filtering on Test)**: Preprocessing rules (e.g. outlier handling) must be implemented causally without leaking full-dataset distribution metrics.

---

## 12. Future Preprocessing Decisions (Documented for Subsequent Tasks)
The following data quality issues documented in Task 2E and 2F are recorded as requiring formal preprocessing decisions in Task 3. **No action is taken in this task**:
1. **Internal Resistance (`IR == 0`)**: 4,922 records (mostly in batteries 87–93) have unmeasured zero resistance. Requires handling via binary indicators (`IR_is_zero`) and cohort median/causal imputation.
2. **Battery 85 Sensor Fault**: `Tmin = -270 °C` and `Tmax = 400 °C` due to hardware open-circuit. Requires imputing sensor bounds using `Tavg` or cohort thermal bounds.
3. **Chargetime Resting Spikes**: 17 records with `chargetime > 60` min (up to ~3,934.7 min / 65.5 hours) representing multi-day lab pauses. Requires clipping or causal forward-filling.
4. **Battery 19 `QCharge` Drift**: Linear coulometer drift from cycle 12 to 39 (1.22 to 1.97 Ah) before resetting. Requires drift adjustment or robust scaling.
5. **Early `SOH > 100`**: Valid electrochemical artifact of 50-cycle baseline; requires preservation or physical upper-bound clipping consideration.

---

## 13. Final Modeling Contract (Locked Architecture)

| Component | Specification |
| :--- | :--- |
| **SOH Target** | $y_{\text{SOH}} = (QDischarge / C_{\text{ref}}) \times 100$ |
| **RUL Target** | $y_{\text{RUL}} = \max(\text{cycle}) - \text{cycle}$ |
| **SOH Primary Features** | `['IR', 'QCharge', 'Tavg', 'Tmax', 'Tmin', 'chargetime', 'cycle']` |
| **RUL Primary Features** | `['IR', 'QCharge', 'Tavg', 'Tmax', 'Tmin', 'chargetime', 'cycle', 'SOH_pred']` |
| **Forbidden Features** | `battery_id`, `RUL` (for SOH), `QDischarge` (for Primary SOH & RUL), ground-truth `SOH` (for RUL) |
| **Splitting Mechanism** | Strict Battery-Grouped (Leave-Batteries-Out) Partitioning |
| **Deployment Mode** | Fast-charge intake screening (zero dependency on full discharge tests) |
