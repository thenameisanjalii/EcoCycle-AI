# EcoCycle AI — Target Definition and Data-Leakage Audit Report

**Dataset Audited**: `C:\Users\patid\Desktop\SecondSpark-AI_ML\master_dataset.csv`  
**Audit Type**: Target Definition, Feature Leakage & Splitting Integrity  
**Mode**: Strict Read-Only  

---

## 1. Executive Summary & Leakage Risk Overview
A rigorous data leakage audit was conducted across all 11 columns of `master_dataset.csv` for both primary estimation targets:
1. **State of Health (`SOH`)**
2. **Remaining Useful Life (`RUL`)**

The audit evaluated five distinct vulnerability vectors:
- **Direct Target Leakage**: Feeding the target or an exact transformation of the target into training features.
- **Derived-Target Leakage**: Features algebraically linked to the target formulation.
- **Temporal Leakage**: Features utilizing observations occurring after the prediction point ($t > t_{\text{current}}$).
- **Identifier Leakage**: Categorical/integer IDs that allow models to memorize individual cell traits or lifespans.
- **Data Splitting Leakage**: Random row-wise train/test partitioning that mixes cycles of the same battery across splits.

---

## 2. In-Depth Target Formulation & Mathematical Dependencies

### Target 1: State of Health (`SOH`)
- **Mathematical Definition** (verified from `build_master_dataset.py`):
  $$\text{SOH}_t = \frac{QDischarge_t}{\overline{QDischarge}_{\text{cycle} \le 50}} \times 100$$
- **Algebraic Identity Risk with `QDischarge`**:
  - The denominator $\overline{QDischarge}_{\text{cycle} \le 50}$ is a **fixed cell-specific constant** for each battery ($C_{\text{ref}}$).
  - Within every single battery in `master_dataset.csv`, the ratio $\frac{\text{SOH}_t}{QDischarge_t}$ has a standard deviation of **$3.77 \times 10^{-14}$ (machine precision zero)**.
  - Globally across all 116,663 records, Pearson correlation $r(QDischarge, \text{SOH}) = 0.9668$.
  - **Audit Verdict**: Feeding `QDischarge` to an ML model to predict `SOH` results in a trivial linear regression (learning multiplier $\approx 92.8$), bypassing electrochemical degradation modeling. In practical fast-charge testing, `QDischarge` is unavailable without running a full discharge test (which itself directly measures capacity, rendering ML redundant).

### Target 2: Remaining Useful Life (`RUL`)
- **Mathematical Definition** (verified from `build_master_dataset.py`):
  $$\text{RUL}_t = \max(\text{cycle}) - \text{cycle}_t$$
- **Exact Linear Correlation with `cycle`**:
  - For every battery, $r(\text{cycle}, \text{RUL}) = -1.0000$ (exact negative correlation).
  - The slope is always $-1.0$, and the intercept is $\max(\text{cycle})$ (the terminal lifespan of that specific cell).
  - **Audit Verdict**: If an ML model is given `cycle` and trained on random row splits, it memorizes the battery-specific intercept $\max(\text{cycle})$, achieving artificial $R^2 > 0.99$. On unseen batteries, this completely collapses.

---

## 3. Data Splitting Leakage Analysis: Random vs. Battery-Aware Splitting

### Why Random Row-Wise Splitting is Catastrophic:
If `sklearn.model_selection.train_test_split(shuffle=True)` is applied to `master_dataset.csv`:
1. **Identifier & Lifespan Memorization**: Rows from all 139 batteries will be interleaved across train and test sets. A tree-based model can easily identify a cell's baseline impedance and memorize its exact $\max(\text{cycle})$.
2. **Temporal Autocorrelation**: Consecutive cycles (e.g. cycle 100 in train, cycle 101 in test) share near-identical sensor noise and thermal conditions, inflating test scores without true generalization.
3. **Reference Capacity Leakage**: For SOH, the cell's constant $C_{\text{ref}}$ is memorized from training cycles and applied to test cycles.

### Mandatory Splitting Strategy:
- **Strict Battery-Grouped Splitting (Leave-Batteries-Out)**:
  - All records for a given `battery_id` must reside **exclusively** in either the Train, Validation, or Test partition.
  - Recommended methods: `GroupKFold`, `GroupShuffleSplit`, or deterministic battery-cohort partitioning (e.g., 70% train batteries [~97 cells], 15% validation batteries [~21 cells], 15% test batteries [~21 cells]).
  - Zero cycles of test batteries may appear in training or validation.

---

## 4. Feature Classification for SOH and RUL

### State of Health (`SOH`) Feature Matrix

| Feature | Classification | Leakage Risk | Prediction-Time Availability | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `IR` | **Allowed** | None | Available during charge | Direct physical measurement of internal cell degradation. |
| `QCharge` | **Allowed** | None | Available at charge end | Total charge delivered; strong indicator of capacity without discharging. |
| `Tavg` | **Allowed** | None | Available at cycle end | Average thermal dissipation during cycle. |
| `Tmax` | **Allowed** | None | Available at cycle end | Peak temperature reflecting internal resistance heating. |
| `Tmin` | **Allowed** | None | Available at cycle end | Minimum thermal baseline. |
| `chargetime` | **Allowed** | None | Available at charge end | Charge duration reflecting acceptance kinetics. |
| `cycle` | **Allowed** | None (with Group split) | Available from BMS | Operating age of the battery. |
| `QDischarge` | **Restricted** | Derived-Target / Proxy | Requires full discharge | $\text{SOH} \propto QDischarge$. If used, model learns trivial scaling. Unavailable in fast-charge intake. |
| `battery_id` | **Forbidden** | Identifier Leakage | Metadata only | Cell ID causes memorization of baseline capacity. |
| `RUL` | **Forbidden** | Temporal / Target Leakage | Unknown | Encodes future terminal lifespan. |
| `SOH` | **Forbidden** | Direct Target Leakage | Ground truth | Target to be predicted. |

---

### Remaining Useful Life (`RUL`) Feature Matrix

| Feature | Classification | Leakage Risk | Prediction-Time Availability | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `IR` | **Allowed** | None | Available during charge | Impedance growth tracks remaining cell life. |
| `QCharge` | **Allowed** | None | Available at charge end | Charge intake capability tracks degradation curve. |
| `QDischarge` | **Allowed** | None | Available if discharged | Measured capacity at cycle $t$. |
| `Tavg` | **Allowed** | None | Available at cycle end | Thermal metric during cycle. |
| `Tmax` | **Allowed** | None | Available at cycle end | Peak thermal metric. |
| `Tmin` | **Allowed** | None | Available at cycle end | Minimum thermal metric. |
| `chargetime` | **Allowed** | None | Available at charge end | Charging duration. |
| `cycle` | **Restricted** | Lifespan Intercept Risk | Available from BMS | $r=-1.0$ per battery. **Allowed ONLY under Battery-Grouped splitting** to prevent EOL memorization. |
| `SOH` | **Restricted** | Upstream Dependency | Requires model estimation | Ground truth SOH is unavailable on unseen batteries. Must use predicted SOH (`SOH_pred`). |
| `battery_id` | **Forbidden** | Identifier Leakage | Metadata only | Memorizes exact EOL per cell ID. |
| `RUL` | **Forbidden** | Direct Target Leakage | Ground truth | Target to be predicted. |

---

## 5. Recommended Prediction-Time Data Availability Assumptions

### Operational Deployment Scenario: EV Battery Second-Life Intake Station
1. **Intake Screening Mode (Fast-Charge Diagnostic)**:
   - Battery pack/module is plugged into a high-rate diagnostic cycler.
   - **Available Telemetry**: `IR`, `QCharge`, `Tavg`, `Tmax`, `Tmin`, `chargetime`, current BMS `cycle`.
   - **Unavailable Telemetry**: `QDischarge` (requires full slow discharge), `SOH` (unknown), `RUL` (unknown).
   - **Recommended SOH Pipeline**: Train SOH model using charge telemetry (`IR`, `QCharge`, `Tavg`, `Tmax`, `Tmin`, `chargetime`, `cycle`).
2. **Two-Stage Cascaded RUL Pipeline**:
   - Stage 1: Predict SOH from diagnostic telemetry $\rightarrow \widehat{\text{SOH}}$.
   - Stage 2: Predict RUL using diagnostic telemetry + $\widehat{\text{SOH}}$ + historical causal rolling slopes.
   - This prevents target leakage and mirrors true operational availability.

---

## 6. Audit Artifacts Generated
- [`reports/data_audit/target_leakage_audit.csv`](file:///C:/Users/patid/.gemini/antigravity/scratch/EcoCycle-AI/reports/data_audit/target_leakage_audit.csv) — Machine-readable evaluation of all 11 features against both targets.
- [`reports/data_audit/target_leakage_audit.md`](file:///C:/Users/patid/.gemini/antigravity/scratch/EcoCycle-AI/reports/data_audit/target_leakage_audit.md) — Comprehensive technical audit document.
