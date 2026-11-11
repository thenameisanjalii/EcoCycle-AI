# Measured discharge SOH extension evaluation

Bundle: `run-20261111-measured-v3.0.0`, version `3.0.0`.
Registry SHA256: `9f47b29571f90c0b42c75d7f66b02032b28ea77acca1d1c3ab7e26251c9fdcb6`.

The original compatible master cohort is unchanged: 116,663 rows, 139 batteries, 74.5527-104.7925% SOH, zero observations in 50-60% or 60-70%. `master_dataset_extended.csv` is an exact preserved copy, not a claim of compatible low-SOH extension.

The new measured-discharge data are kept separately in `ml/data/wheeler2025_discharge_measured.csv`. The 50C C/3 characterization protocol is incompatible with the original cycling telemetry. All results below apply only to this separate research cohort.

SOH = measured C/3 discharge capacity / documented pristine cycle-0 C/3 discharge reference at the same 50C chamber setting * 100. The reference follows 25 documented wake-up cycles. No charge capacity, nominal rating, interpolated capacity, or degraded first observation substitutes for this discharge reference.

Acquisition: 232 valid measurements from 20 independent cells, 3 excluded. Fixed sampling: cycle 0, every 400 cycles, final characterization. Measured SOH spans 31.4499-100.0000%.

## Grouped evaluation

Cells are partitioned within the seven source aging protocols before inspecting labels: one train and one test cell per protocol, plus one validation cell for each three-replicate protocol. Seed 42. Cells never cross partitions. The protocols are shared across partitions, so this measures held-out cells under known laboratory protocols, not unseen protocols or deployment performance.

Ridge scaling/imputation, feature support, and all estimator fitting use train cells only. Hyperparameters, early stopping and family selection use validation only. No refit on validation; test is evaluated only after selection. History uses only supplied, strictly preceding observations and actual cycle gaps. Missing history remains missing before train-only Ridge imputation; no unmeasured sensor is introduced.

| Partition | Cells | Rows | SOH min/max | 50-60% rows/cells | 60-70% rows/cells |
|---|---:|---:|---|---|---|
| train | 7 | 81 | 42.11/100.00 | 16/6 | 16/7 |
| validation | 6 | 71 | 41.28/100.00 | 15/5 | 12/6 |
| test | 7 | 80 | 31.45/100.00 | 17/7 | 16/7 |

## Measured SOH errors

Errors are percentage points; intervals are lower-inclusive and upper-exclusive. Independent cell counts are per interval and cannot be added across intervals. Empty intervals have null error, never a fabricated score.

| Contract (selected family) | Test interval | Rows | Cells | MAE | RMSE |
|---|---|---:|---:|---:|---:|
| single (ridge) | overall | 80 | 7 | 0.7375 | 0.9615 |
| single (ridge) | [0,50) | 11 | 3 | 0.7988 | 1.0650 |
| single (ridge) | [50,60) | 17 | 7 | 0.7354 | 0.9078 |
| single (ridge) | [60,70) | 16 | 7 | 0.5710 | 0.7755 |
| single (ridge) | [70,80) | 10 | 6 | 0.7894 | 1.0158 |
| single (ridge) | [80,90) | 13 | 7 | 0.7152 | 0.9330 |
| single (ridge) | [90,110) | 13 | 7 | 0.8755 | 1.1169 |
| history (ridge) | overall | 73 | 7 | 0.6662 | 0.8343 |
| history (ridge) | [0,50) | 11 | 3 | 0.3108 | 0.5082 |
| history (ridge) | [50,60) | 17 | 7 | 0.6699 | 0.7960 |
| history (ridge) | [60,70) | 16 | 7 | 0.6711 | 0.8291 |
| history (ridge) | [70,80) | 10 | 6 | 0.8634 | 0.9660 |
| history (ridge) | [80,90) | 13 | 7 | 0.7022 | 0.8507 |
| history (ridge) | [90,110) | 6 | 6 | 0.8881 | 1.1153 |

## Errors per independent test battery

| Contract | Battery | Rows | MAE | RMSE |
|---|---|---:|---:|---:|
| single | wheeler2025:Cell1b | 10 | 0.7273 | 0.7669 |
| single | wheeler2025:Cell2c | 9 | 0.2745 | 0.3910 |
| single | wheeler2025:Cell3a | 11 | 0.2113 | 0.2349 |
| single | wheeler2025:Cell4c | 12 | 1.5437 | 1.5579 |
| single | wheeler2025:Cell5b | 12 | 0.9758 | 1.0654 |
| single | wheeler2025:Cell6a | 17 | 0.2021 | 0.2454 |
| single | wheeler2025:Cell7a | 9 | 1.4732 | 1.5752 |
| history | wheeler2025:Cell1b | 9 | 0.7108 | 0.7607 |
| history | wheeler2025:Cell2c | 8 | 0.5176 | 0.5711 |
| history | wheeler2025:Cell3a | 10 | 0.3096 | 0.3386 |
| history | wheeler2025:Cell4c | 11 | 1.4792 | 1.4995 |
| history | wheeler2025:Cell5b | 11 | 0.8662 | 0.9094 |
| history | wheeler2025:Cell6a | 16 | 0.2043 | 0.3152 |
| history | wheeler2025:Cell7a | 8 | 0.7417 | 0.8965 |

## Primary and second life

An observed SOH below 80% indicates crossing a conventional primary-life capacity threshold; it does not imply zero useful second-life service. With sparse characterization, the primary crossing is interval-censored between observations (or left-censored for an already-degraded start), never interpolated or assigned a fabricated exact cycle. Noncrossing observations are right-censored.

No application-specific second-life service endpoint is established by this data. No second-life RUL estimator is trained, and API RUL is always null. Recorded ends are retained as censored follow-up with endpoint unknown. `trajectories.csv` explicitly retains these states. Choosing an arbitrary 60% endpoint would not establish service failure.

## Verification and limitations

Exact API/offline parity passed for all 80 held-out single records and all 7 held-out histories, reversed on input. Latest history predictions also match saved test predictions. 131 original file hashes verified unchanged.

This is a small, sparse, single-laboratory research evaluation, with seven independent test cells. Charge and discharge capacity are strongly related during this controlled characterization; the reported errors are not proof of field accuracy, calibrated uncertainty, safety, or transfer to other protocols. Aging chamber temperature is controlled at 50C, but cell temperature was not measured. No IR or temperature channels are invented. Existing source licensing was not independently revalidated; original data are retained without relicensing. The new source explicitly states CC BY 4.0 in dataset V2 metadata and README. Source attribution, acquisition and exclusions are documented in `reports/soh_extension/README.md`.

All candidate validation/test metrics, per-battery errors and range errors are retained in the immutable bundle. No change to the existing frontend default or v2 bundle is made: its 50-70% accuracy remains unsupported. The new `/v3/predict` API requires explicit `domain: wheeler_C3_50C` and is a separate opt-in research contract.
