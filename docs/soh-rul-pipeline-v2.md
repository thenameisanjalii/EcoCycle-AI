# SOH/RUL pipeline v2

The supported measurement API is `POST /v2/predict`. The frontend uses it. The
original models and CSVs remain unchanged; legacy prediction/decision routes
remain available with deprecation and target-definition response headers.

## Definitions and independent audit

`master_dataset.csv` contains 116,663 rows, 139 batteries and no duplicate
battery/cycle keys. Its SHA-256 remains
`0affa1f6084edf7bba9b99736267a14d6fb693de72b16220be6400bcb035ec88`.
Measured stored SOH spans **74.5527286641–104.7924528495%**. There are **zero**
examples below 70%, and none below 74.5527%.

The existing labels are preserved exactly:

```text
C_ref(cell) = mean(QDischarge for that cell at recorded cycle <= 50)
SOH = QDischarge / C_ref(cell) * 100
legacy RUL = last recorded cycle(cell) - current cycle
```

The independently reconstructed SOH differs by at most 7.11e-14 percentage
points; reconstructed legacy RUL matches every row exactly. This is an empirical
early-life discharge reference, not rated capacity. SOH above 100% is allowed.
For early observations the reference includes subsequent observations, so it is
an offline label definition only: **the reference and discharge capacity never
enter the learned feature matrix**. Battery ID is grouping/metadata only.
No birth measurement, inferred reference capacity or first-50-cycle statistics
are required at inference.

`QCharge` is measured charge throughput in Ah. It correlates with discharge
capacity here, but is not a measured discharge-capacity replacement. If a user
has measured discharge capacity and a defensible reference, the capacity ratio
can be computed directly under that reference; a nominal-capacity ratio is a
different target from this model's labels. Neither is silently substituted.

Low-QCharge stress tests on the original model show tree extrapolation plateaus.
The plateau depends on the fixed measurements and history; **a universal ~81%
value is not independently established**. Stress tests intentionally change
only present charge capacity on archived feature rows, with no invented target
or historical measurements. They are diagnostics, not degraded-cell accuracy.

## Input contracts

Send only actual measurements. Units are IR in ohms, charge capacity in Ah,
temperatures in Celsius, charge time in **minutes**, and operating cycle count.
`QDischarge`, SOH/RUL labels, future endpoints and client-engineered features are
rejected. The frontend and HTTP API require every numeric measurement and a
nonempty Battery ID. Missing, null, nonnumeric, nonfinite and out-of-range
measurements are rejected before inference. Battery ID may be a string or
integer, is trimmed when textual, and is not restricted to dataset IDs.

Both validators read `configs/prediction_input_bounds.json`, derived from all
116,663 master-dataset rows by `python scripts/derive_input_bounds.py`:

| Input | Minimum (inclusive) | Maximum (inclusive) | Input step |
| --- | ---: | ---: | --- |
| IR (ohms) | 0.0096521955 | 0.022639817 | Any decimal |
| QCharge (Ah) | 0.82887155 | 1.9679104 | Any decimal |
| Tavg (C) | 25.03826830669143 | 41.44028639388188 | Any decimal |
| Tmax (C) | 25.938044 | 44.662853 | Any decimal |
| Tmin (C) | 23.404068 | 36.69121943252374 | Any decimal |
| Charge time (minutes) | 6.474444999999832 | 3934.7051666666666 | Any decimal |
| Cycle | 1 | 2237 | Whole numbers (1) |

The audit excludes missing/nonfinite/nonpositive measurements and fractional
cycles. Zero IR excludes 4,922 readings. All three temperature readings are
excluded for the 123 faulty triplets: zero/dropout readings, saturation values
outside (0, 100) C, or inconsistent Tmin/Tavg/Tmax ordering. This also excludes
the corrupted averages associated with saturated sensors. Bounds use the
remaining original values at full precision; decimal inputs use `step="any"`
so valid recorded endpoints are not rounded or rejected by browser step rules.
Recorded charge-time holds and charge-capacity drift are retained: these are
observations, not null/sentinel codes. The bounds file records the dataset hash
and exclusion counts. Raw datasets and trained preprocessing are unchanged.

```json
{
  "contract": "single",
  "records": [
    {"battery_id": "cell-A", "cycle": 120, "QCharge": 1.05, "IR": 0.016,
     "Tavg": 34, "Tmin": 31, "Tmax": 38, "chargetime": 10.3}
  ]
}
```

The numeric JSON above illustrates units, not a labeled evaluation example.
Measured CSV examples are in `examples/pipeline_v2/`.

- **single**: one or more independent assessments; outputs one SOH per row,
  with `rul: null`. The HTTP contract requires all seven numeric inputs within
  the ranges above and a nonempty Battery ID. A batch of one is supported.
  No historical features enter this model.
- **history**: at least two observations from exactly one identified battery.
  Order is normalized internally; only the latest cycle is returned. Distinct
  batteries must be submitted separately. Duplicate cycles within a battery
  are rejected rather than silently aggregated. Cycle gaps are allowed for
  feature generation; deltas use the actual gap.

The history model uses up to five **strictly preceding supplied observations**
for rolling means/standard deviations and previous observed measurements for
lags. Missing previous readings remain NaN. The first observed row has no lag,
delta or historical mean. There is no fabricated birth reference; span/count
describe only the submitted window. Arbitrarily truncated histories differ
from the full-trajectory training distribution, so the API flags late-starting
and short windows for review. The history evaluation excludes first rows,
matching the API's two-observation minimum.

Results contain raw predictions, separately bounded display values, metadata,
the registry checksum, exact target definitions and reliability warnings.
Clipping is only for display. Checks flag input values outside train-only
support, imputed sensors and time/temperature faults. These checks do not
constitute calibrated uncertainty. The warnings explicitly state that 50–70%
SOH accuracy is unsupported. The frontend clears prior outputs on edit,
upload, deletion, sample replacement and failed/new submission, and aborts or
ignores responses for outdated inputs.

## Shared preprocessing and charge-time investigation

The HTTP checks above run before inference. Offline preprocessing still supports
faulted or missing archived readings for training and historical diagnostics.
`MeasurementPreprocessor` is the sole v2 cleaning/feature implementation for
training, offline inference and HTTP inference. It is fit on training batteries
only and serialized with the model. Validation/test never update its state.

- IR equal to zero is flagged as a sensor fault and made missing. Negative IR
  and physically impossible charge capacity/time/cycle values are rejected.
- Temperature faults depend on readings, never battery ID: missing/zero values,
  values outside [-30, 100] C, `Tmin > Tavg` or `Tavg > Tmax` mark
  the temperature triplet missing. Zero-temperature treatment is specific to
  this room-temperature lab protocol, not a universal thermocouple rule.
- Faulted current sensors use per-battery past-only forward fill when history
  exists, then train-only medians. Single assessments use train-only medians.
  Missingness flags always describe the original readings. Historical features
  use actual observed sensor values; imputed values never become fake lags.
- The CSV has 4,922 zero-IR readings and 123 temperature-fault/zero rows under
  this rule. The charge-time median is 10.3143, q99 22.0750, q99.5 24.2157 and
  maximum 3934.7052; 17 rows exceed 60. The audit lists their cells/cycles.
  The repeated ~3933–3935 spikes span multiple cells near cycles 48–77.
  These are not evidence for converting an entire battery from seconds.
  Repository provenance calls the units minutes; raw instrument/protocol data
  needed to independently confirm units and explain pauses are absent.
- Nonpositive charge times and values above the **training** q99.5 are marked
  missing and flagged. No guessed unit conversion or target-dependent removal
  occurs. This is a conservative modeling rule, not proof those readings are
  instrument faults. The fitted threshold and medians are in preprocessing.json.

## Failure endpoint and censoring

Default failure is confirmed SOH **strictly below 80%** on **three consecutive
numbered observed cycles**. A gap or SOH >= 80% resets the run. The endpoint is
the third qualifying cycle (confirmation time), with no backdating. Both the
threshold and confirmation count are training CLI parameters stored in the
bundle. This threshold is relative to the existing SOH reference above, not to
manufacturer-rated capacity.

New labels are kept separately as `RUL_endpoint = confirmation_cycle - cycle`
for at-risk observations on confirmed-failure trajectories. Rows after the
event are excluded from regression. The three confirmation observations remain
pre-event/at-event by the chosen endpoint convention, including zero RUL at
confirmation. Ground-truth SOH is used only to construct offline endpoints,
never as an inference feature.

The default rule finds **39 observed failures and 100 right-censored cells**:
train 23 events/74 censored; validation 11/10; test 5/16. Censored cells retain
recording-end censor times and observed follow-up lower bounds, with missing
RUL labels. Their recording ends are never labeled as failures. They remain
available for SOH training and in `trajectories.csv`.

RUL here is regression **conditional on the confirmed-event cohort**. It excludes
censored trajectories from its loss and therefore has selection bias; it is
not a population survival model and cannot certify remaining life for a
censored/deployment population. A survival-aware model using event indicators,
follow-up and censoring assumptions is additional work requiring endpoint and
withdrawal metadata. Absence of confirmation means no observed event under this
rule, not proof the cell remained healthy indefinitely.

## Training, evaluation and reproducibility

Battery groups, not rows, are shuffled with seed 42. Counts derive from cohort
size and configurable fractions, giving 97/21/21 for this CSV. This default
matches the original cohort split, enabling legacy comparison on held-out
cells. Test labels never select parameters, iteration count or model family.

Each of `single_soh`, `history_soh`, and `history_rul` compares:

- A ridge baseline with train-only median/missing-indicator processing and
  scaling; validation selects alpha from 1 and 100.
- XGBoost depths 4/7, learning rate .05, up to 500 iterations, validation RMSE
  with 35-round early stopping.
- CatBoost depths 4/7, learning rate .05, up to 500 iterations, validation RMSE
  with 35-round early stopping.

All fixed settings and seeds are in the source snapshot and config; tuning
results and selected model parameters are serialized. Models are not refit
on validation. The validation-selected RUL family is retained even though
another candidate has lower test error. RUL's five event test cells make
generalization conclusions weak.

The [measured evaluation](../reports/pipeline_v2/run-20261111-v2.0.1/evaluation.md)
contains family comparisons, same-row legacy comparisons, SOH MAE/RMSE by range,
RUL errors by life stage, cohort counts and partial-history diagnostics. Full
per-battery metrics, macro battery MAE, validation/test predictions and
cross-target legacy diagnostics are in the bundle. Legacy RUL predicts a
different endpoint, so its original-target errors are reported separately;
they cannot establish improvement on confirmed-failure RUL.

SOH coverage stops at the actual observed minimum. An aggregate 70–80% error
does not validate 70–74.55%, and no 50–70% accuracy is claimed. The test split
has only 96 rows below 80% SOH. Repeated rows within one cell are correlated,
so row counts should not be confused with independent battery evidence.

Every completed run has its own non-overwritable directory, bundling selected
models, fitted preprocessing, feature order/units, exact dependencies, dataset
and original-artifact hashes, splits, endpoint definitions, tuning, metrics,
predictions and training/inference source snapshots. Registry SHA-256 covers
the registry, which hashes all bundle files. Loading checks file hashes,
pipeline version, critical dependency versions, feature schemas and runtime
preprocessing/inference source compatibility. Checksum integrity assumes a
trusted local artifact source; it is not an artifact signature.

## Exact commands (PowerShell, repository root)

Use Python 3.13 for the included reference bundle. Other environments can train
their own new versioned bundle. For the included bundle's exact core environment:

```powershell
python -m pip install -r ml/artifacts/pipeline_v2/run-20261111-v2.0.1/requirements-lock.txt
```

Train a new run, choosing an output directory that does not exist:

```powershell
python -m ml.pipeline_v2.train --dataset ml/data/master_dataset.csv --output ml/artifacts/pipeline_v2/my-run --seed 42 --train-fraction 0.70 --validation-fraction 0.15 --threshold 80 --confirmation 3 --iterations 500 --threads 4
```

The included measured run used the same defaults:

```powershell
python -m ml.pipeline_v2.train --output ml/artifacts/pipeline_v2/run-20261111-v2.0.1 --iterations 500 --threads 4
```

That path now exists, so rerunning that exact command deliberately refuses to
overwrite it. Choose `my-run` for a new execution.

The backend defaults to the included
`ml/artifacts/pipeline_v2/run-20261111-v2.0.1` bundle, resolved relative to the
repository rather than the terminal's current directory. You can start it with:

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Set `ECOCYCLE_V2_BUNDLE` to explicitly select another completed, compatible
bundle. An invalid explicit selection returns 503; it does not fall back to
another model. Restart the server when changing this selection:

```powershell
$env:ECOCYCLE_V2_BUNDLE = (Resolve-Path 'ml/artifacts/pipeline_v2/run-20261111-v2.0.1').Path
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal, from the repository root:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

The frontend defaults to `http://localhost:8000`; set `VITE_API_BASE_URL` before
starting it when using another host. `npm.cmd` avoids PowerShell's `npm.ps1`
execution-policy restriction. No dependency downloads were needed in the
verification environment.

Offline inference and a reproducible parity/evaluation report:

```powershell
python -m ml.pipeline_v2.inference --bundle ml/artifacts/pipeline_v2/run-20261111-v2.0.1 --input examples/pipeline_v2/single.csv --contract single --output single-prediction.json
python -m ml.pipeline_v2.inference --bundle ml/artifacts/pipeline_v2/run-20261111-v2.0.1 --input examples/pipeline_v2/history.csv --contract history --output history-prediction.json
python -m scripts.verify_pipeline_v2 --bundle ml/artifacts/pipeline_v2/run-20261111-v2.0.1 --output reports/pipeline_v2/my-verification
```

Prediction JSONs and report directories also refuse to overwrite existing
outputs. The parity verifier compares every held-out single assessment and
every held-out complete history against the same offline entry point, checks
saved predictions and verifies original artifact/data hashes. The reference
artifact tests use the included bundle; without it those artifact-specific
tests are skipped and training/causality tests still run.

```powershell
python -m pytest -q -p no:cacheprovider
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
```

## Further measured data needed

Collect independent discharge capacity and defensible reference measurements
across 50–70% SOH and lower, with multiple cells per range and repeated operating
conditions. Extend trajectories through confirmed endpoints; record reasons for
stopping/censoring, replacements, resets and missing cycles. Supply instrument
unit/calibration metadata and charge/rest protocol logs, particularly for time
spikes. Include chemistry, nominal/rated capacity, charge policy, load and
temperature coverage, plus field histories with realistic missingness and
window lengths. Independent external-cell validation and calibrated prediction
intervals are needed before reliable field-life or degraded-range claims.
