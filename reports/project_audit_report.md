# EcoCycle-AI — ML Project and Data Audit Report

**Audit scope:** repository structure, committed datasets, feature/target definitions, preprocessing, model artifacts, registry, and FastAPI inference surfaces.

## Executive verdict

The project has a sensible high-level ML/API separation and the checked-in partition files are cleanly battery-grouped. The packaged artifacts and API contract are internally consistent **for already-engineered 32-feature records**; the test suite passes (`85 passed`).

The end-to-end project is **not presentation-ready without corrective work**, because the repository does not contain a runnable, reproducible path from the committed 19-column datasets to the 32-feature models. The independent static audit also fails because it expects the absent `ml/data/master_dataset.csv`.

## Project Structure Health

### Strengths

- `backend/routes`, `backend/services`, and `backend/schemas` provide a clear API/business/schema separation.
- `ml/preprocessing`, `ml/models`, `ml/data`, and `ml/artifacts` are recognizable ML engineering boundaries.
- `configs/final_model_registry.json` records model feature lists, metrics, artifact paths, and hashes.
- `FinalModelRegistry` verifies artifact SHA-256 values before loading.
- Train/validation/test files are present for both targets and use disjoint battery groups.

### Structural risks

- `ml/training/` and `ml/evaluation/` are empty in the repository; the baseline training code is under `ml/models/`, and no committed advanced-model training entry point consumes the partition CSVs.
- `configs/data_config.yaml` refers to `ml/data/raw`, `ml/data/interim`, and `ml/data/features`, but those inputs/outputs are not the actual committed training layout.
- `ml/models/config.py` and `test_task_2m_1_static_audit.py` require `ml/data/master_dataset.csv`, which is absent. Running the static audit therefore fails with `FileNotFoundError`.
- Runtime model binaries and preprocessors exist locally but are ignored by `*.joblib`; a fresh clone cannot reproduce the API unless these artifacts are supplied out-of-band.
- `Dockerfile` and `docker-compose.yml` start `backend.app.api.main:app`, but the repository entry point is `backend.main:app`. Container startup is therefore miswired.
- The same feature definitions are duplicated in `feature_schema.py`, `feature_engineering.py`, and `models/config.py`, creating drift risk.
- `CausalBatteryPreprocessor` contains a hard-coded battery-specific rule (`battery_id == 85`) and fixed split cardinalities are embedded in `get_battery_splits`; these are acceptable for this frozen dataset only, not for general reuse.

## Data & Feature Assessment

### Dataset schema found

Each committed partition has **19 columns**:

- **Metadata:** `battery_id`
- **17 baseline model features:** `IR`, `QCharge`, `Tavg`, `Tmax`, `Tmin`, `chargetime`, `cycle`, `IR_is_zero`, `temp_sensor_fault`, `IR_lag1`, `IR_delta`, `QCharge_lag1`, `QCharge_delta`, `Tavg_lag1`, `Tavg_delta`, `chargetime_lag1`, `chargetime_delta`
- **Target:** `SOH` in the SOH files, or `RUL` in the RUL files

The locked production registry and API require **32 features**, adding:

`IR_accel`, `QCharge_accel`, `Tavg_accel`, `chargetime_accel`, `thermal_dissipation_rate`, `charge_efficiency_proxy`, `resistance_growth_ratio`, the six 5-cycle rolling statistics, `cum_capacity_fade_rate`, and `cum_resistance_growth_rate`.

The repository does contain `generate_causal_features_dataset()`, but it is not called by `ml/preprocessing/pipeline.py`, any committed training entry point, or the API. Consequently, the committed CSVs cannot be passed directly to the locked models or `/predict`.

### Targets and leakage

- **SOH:** target range is approximately `74.55–104.79%`. The documented definition is based on `QDischarge`, so excluding `QDischarge` from model features is correct; including it would make SOH nearly a direct capacity reconstruction.
- **RUL:** target range is `0–2236` cycles and is defined as terminal cycle minus current cycle. This is valid only with battery-grouped evaluation; row-wise random splitting would leak battery lifespan.
- `battery_id`, `QDischarge`, target columns, terminal/future-cycle fields, and cross-target labels are correctly excluded/rejected by the feature schema and input validator.
- The 139 batteries are isolated across 97 train, 21 validation, and 21 test batteries with zero observed overlap. All six partition files contain 116,663 rows in total.
- Data quality is not entirely clean: 4,922 zero-IR records, 8 negative `Tavg` records, 24 zero `Tmin` records, extreme `Tmax`/`Tmin` values, and highly skewed `chargetime` are documented. The preprocessing policy addresses these, but the executable pipeline gap prevents independently reproducing the result from this checkout.

## Pipeline Integrity

| Stage | Assessment |
|---|---|
| Partitioned data | **Pass:** files exist, targets are present, row counts and battery isolation are consistent. |
| Baseline preprocessing | **Partial:** preprocessing creates the 17-feature baseline, with train-derived imputation parameters, but does not produce the 15 advanced features. |
| Advanced feature generation | **Partial:** implementation exists and is intended to be causal, but is not wired into preprocessing/training/API input construction. |
| Training source path | **Fail:** no committed advanced training runner establishes how the locked 32-feature artifacts were produced from the committed CSVs. |
| Artifact registry/loading | **Pass locally:** registry hashes and model feature counts agree; model loading tests pass. |
| API inference | **Pass for supplied 32-feature payloads:** validation, leakage rejection, prediction, and batch behavior are tested. **Fail as an end-to-end data path:** API requires clients to provide all derived features. |
| Deployment | **Fail:** Docker references a nonexistent module path. |

The reported advanced models also regress against their baseline on the held-out test set: SOH RMSE `0.7084` vs baseline `0.5896`, and RUL RMSE `186.36` vs baseline `174.33`. This does not invalidate the project, but the presentation must not describe the advanced models as an unqualified improvement.

## Critical Action Items

- Wire the canonical preprocessing flow so each partition is transformed from the 17 baseline columns into the exact 32-column registry order before training and inference; add a real training/evaluation entry point or clearly preserve the reproducible training command and inputs.
- Resolve the missing raw-data contract: either include the source dataset required by `config.py`/the static audit or change the audit/configuration to use the committed partition files and verify their hashes.
- Make model artifacts reproducible for a fresh checkout: provide the required artifacts through the project’s documented delivery mechanism and record their exact dependency/runtime versions.
- Fix `Dockerfile` and `docker-compose.yml` to launch `backend.main:app`, then run a container smoke test.
- Centralize the feature schema and use it in preprocessing, training, registry validation, and API validation to prevent 17-vs-32 feature drift.
- Re-run final test evaluation after the above wiring is fixed and present the baseline comparison honestly; do not claim advanced-model superiority while its test RMSE is worse.

