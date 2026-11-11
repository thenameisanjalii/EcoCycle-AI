# EcoCycle-AI v2 measured evaluation

Bundle: `run-20261111-v2.0.1`; registry SHA-256: `72b52eda2ff4c0e90226b6d46ad983c0c54567858a8cfdd23ea3f03ec53023be`.

Battery-grouped 70/15/15 split, seed 42; all tuning and early stopping used validation only. No refit on validation. Histories require at least two observations.

| Task | Family | Validation RMSE | Test MAE | Test RMSE | Test rows |
|---|---|---:|---:|---:|---:|
| single_soh | ridge | 1.2485 | 0.6820 | 1.0678 | 18512 |
| single_soh | xgboost (selected) | 0.6844 | 0.3393 | 0.5877 | 18512 |
| single_soh | catboost | 0.7629 | 0.4146 | 0.6902 | 18512 |
| history_soh | ridge | 1.1856 | 0.6555 | 1.0473 | 18491 |
| history_soh | xgboost (selected) | 0.5830 | 0.3127 | 0.5025 | 18491 |
| history_soh | catboost | 0.7028 | 0.3388 | 0.5867 | 18491 |
| history_rul | ridge | 169.4354 | 144.2167 | 179.7249 | 2276 |
| history_rul | xgboost | 111.9107 | 27.3956 | 32.7022 | 2276 |
| history_rul | catboost (selected) | 95.3074 | 44.5404 | 54.8950 | 2276 |

SOH errors are percentage points; RUL errors are cycles. The selected models are determined by validation RMSE even when another candidate has lower test error.

## Same-row legacy SOH comparison

| New task | Rows | New MAE / RMSE | Legacy MAE / RMSE |
|---|---:|---|---|
| single_soh | 18512 | 0.3393 / 0.5877 | 0.3541 / 0.7084 |
| history_soh | 18491 | 0.3127 / 0.5025 | 0.3543 / 0.7088 |

The default grouped cohort reproduces the legacy split. Only archived held-out rows are compared; the archived feature representation is preserved. Single assessment and history are different contracts, so this is not an isolated algorithm-only experiment.

## SOH support and error by range

No measured examples below 74.5527% exist in this CSV. Both 0–50% and 50–70% are unsupported; 70–80% only represents its observed upper portion.

| SOH interval | Single rows | Single MAE / RMSE | History rows | History MAE / RMSE |
|---|---:|---|---:|---|
| [0,50) | 0 | Unsupported | 0 | Unsupported |
| [50,70) | 0 | Unsupported | 0 | Unsupported |
| [70,80) | 96 | 1.4603 / 2.0368 | 96 | 0.6920 / 0.9290 |
| [80,90) | 1798 | 0.6731 / 0.9637 | 1798 | 0.5619 / 0.8039 |
| [90,100) | 15094 | 0.3060 / 0.5265 | 15075 | 0.2836 / 0.4521 |
| [100,110) | 1524 | 0.2044 / 0.3045 | 1522 | 0.2827 / 0.4750 |

## RUL censoring and life stage

Event: third consecutive numbered observed cycle strictly below 80% existing SOH, dated at confirmation. Gaps reset confirmation. Post-event rows are excluded; recording end is not failure.

split       event_observed
test        False             16
            True               5
train       False             74
            True              23
validation  False             10
            True              11

Censored cells retain follow-up lower bounds in trajectories.csv but do not enter this regression loss. These estimates are conditional on observed failure, with selection bias; they are not validated population survival estimates. Only five confirmed-event test batteries support the RUL evaluation.

| Stage (cycle / event cycle) | Rows | MAE / RMSE (cycles) |
|---|---:|---|
| early | 745 | 49.8496 / 55.4022 |
| middle | 753 | 48.5866 / 62.4707 |
| late | 778 | 35.5401 / 45.8187 |

Archived RUL on its original recording-end target: MAE 125.0178, RMSE 186.3573 cycles. The new target is different; a direct RUL accuracy improvement claim is invalid. See legacy_comparison.json for explicitly labeled cross-target diagnostics.

## Limited-history diagnostic

Fixed 5/20-observation windows are evaluated only at recording end, not across all ages. This is a distribution-shift check, not the full-trajectory metric above. No tuning used these results.

- Last 5 observations, 21 test batteries: SOH MAE 0.9226, RMSE 1.1895 percentage points.
- Last 20 observations, 21 test batteries: SOH MAE 0.9297, RMSE 1.1922 percentage points.

## Verification and remaining data needs

Exact API/offline parity passed for 18512 held-out single assessments and 21 complete histories (reversed on input). Latest history predictions also match saved test predictions. Original data/model hashes are unchanged.

The low-capacity stress test confirms tree extrapolation plateaus, but does not establish a universal ~81% value: predictions depend on the other measurements/history. No low-capacity stress input has an invented SOH label.

Needed: independently measured discharge/reference capacities across 50–70% and lower SOH, multiple cells and protocols; long trajectories continuing to confirmed endpoints; censoring/withdrawal reasons and deployment histories with varied window lengths; original charge-time logging/protocol records, instrument calibration and unit metadata; independent chemistry, temperature and load cohorts. Charge time is assumed minutes from repository provenance, not independently confirmed from raw instruments. No reliable degraded-range accuracy or calibrated confidence intervals are claimed.

Detailed per-battery metrics, SOH intervals and RUL stages are in the hashed metrics.json; candidate settings and early stopping are in tuning.json. This report is tied to the registry hash above.
