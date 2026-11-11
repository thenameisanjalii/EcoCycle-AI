# Measured SOH extension: provenance and reproduction

Work branch: `extend-measured-soh-50-70`. Started from
`improve-soh-rul-pipeline` on 2026-11-11. The original CSVs, model bundles and
registries are preserved; their SHA256s are in `preservation_manifest.json`.
No original model is overwritten or promoted. Final numerical results and
API parity evidence are recorded in `verification/evaluation.md` and
`verification/parity.json`.

Acquisition retained 235 original characterization members (822.6 MB
compressed locally); 232 pass protocol checks. The discharge cohort spans
31.4499-100% SOH, with 48 rows from 18 cells at [50,60)% and 44 rows from
20 cells at [60,70)%. Exclusions: Cell2b at 1600 and 3300 cycles and Cell2c
at 1200 cycles began discharge below the protocol voltage check threshold.
CSV blocks were sorted by recorded step time before these checks.

The split contains 7 train cells/81 rows, 6 validation cells/71 rows, and
7 test cells/80 rows. Validation selects Ridge for both contracts. History
test MAE/RMSE is 0.6662/0.8343 percentage points overall (73 rows),
0.6699/0.7960 at [50,60)% (17 rows), and 0.6711/0.8291 at [60,70)%
(16 rows). Both range evaluations contain seven independent test cells.
Single-assessment overall test MAE/RMSE is 0.7375/0.9615 (80 rows).
Per-battery results and all model-family metrics are retained in
`ml/artifacts/pipeline_v3/run-20261111-measured-v3.0.0/metrics.json`.

## Original data and compatible coverage gap

`ml/data/master_dataset.csv`: 116,663 rows, 139 independent batteries,
74.5527286641-104.7924528495% measured SOH. There are no 50-60% or 60-70%
observations. Existing labels divide measured discharge by the documented
per-cell mean discharge capacity at recorded cycles <=50. They are retained
exactly. Battery reference metadata are in `existing_battery_references.csv`.
The older provenance report contains assertions about instruments and faults
that were not independently re-established by this work.

`ml/data/master_dataset_extended.csv` is a separate exact copy of this
compatible cohort. **No verified compatible measurements were appended.**
The new measured low-SOH cohort is separate, not silently pooled into this
CSV or the production frontend. This filename does not imply extended
coverage under the original protocol. Original dataset licensing was not
independently reverified and no new license is applied to existing data.

## Obtained public measurements

Wheeler, William; Venet, Pascal; Bultel, Yann; Sari, Ali (2025),
[Aging study on twenty A123 18650 Graphite/LFP 1.1 Ah cells](https://doi.org/10.57745/OLBXKT),
Recherche Data Gouv, **V2.0** (released 2025-03-11).
Methods: Wheeler, W., Bultel, Y., Venet, P. & Sari, A.,
[An ageing study of twenty 18650 lithium-ion Graphite/LFP cells in first and second life use](https://pmc.ncbi.nlm.nih.gov/articles/PMC11885844/),
Scientific Data 12, 392 (2025), DOI 10.1038/s41597-025-04712-7.

Dataset V2 `termsOfUse` and the 2025-03-06 README explicitly specify
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution and
transformation details are retained here and in each measured CSV row. The
publisher's MATLAB example says CC-BY in its text/header but includes a
BY-SA hyperlink in a comment. It was inspected to identify its charge-based
labels, retained unchanged, and its code is not incorporated into our parser.
The governing dataset metadata and README agree on CC BY 4.0.

The source is a different experiment from Severson 2019: acquisition in
2020-2022, distinct source cell IDs, authors/laboratories, cycling protocols,
and source files. No shared-cell identity was found. New IDs are namespaced
`wheeler2025:Cell1a` through the twenty actual cells (there is no Cell3c).
Source IDs, original member paths, public archive download URLs, published
archive MD5, member CRC32, compressed and decompressed SHA256 are retained.
Duplicate battery/cycle keys and duplicate source content are rejected.
Published whole-archive MD5s are recorded, **not independently verified**:
only selected members were downloaded. Each downloaded ZIP member's CRC
and uncompressed length are verified, and its SHA256 is computed locally.

Chemistry/capacity: A123 18650 LFP/graphite, rated 1.1 Ah. Aging and
intermediate characterization at a 50C chamber setting, with an initial
documented 25-cycle wake-up procedure. Cell surface temperature was **not
measured**. Seven aging protocols vary CC/CC-CV charge, 3.55/3.65 V charge
limit, C/3 versus 2C rates, WLTP versus constant-current discharge, and
70%/100% depth of discharge. Raw characterization uses C/3 discharge step
11 and C/3 charge step 13; discharge reaches 2.5 V. Instrument current is
in A, voltage V, capacity Ah, step time seconds. Charge time is converted
to minutes by dividing recorded step duration by 60. These units and
step numbers are documented in the article's Methods and Table 4.

The publisher's convenient `extractedData.mat` **cannot supply the target**:
its `charac.chargecapacity` and published SOH use charge capacity from step
13. Its aging fields are block totals, not individual full-discharge
capacities. None is treated as measured discharge or an SOH label.

Instead, `fetch_wheeler_characterizations.py` obtains raw CSV ZIP members
using standard HTTP ranges. Sampling was fixed before discharge labels
were extracted: cycle 0, every 400 aging cycles, and each cell's final
characterization. All twenty cells are included without selecting for SOH.
Raw members remain locally in `raw_characterizations/*/*.deflate` (ignored
by Git because of size); their source URLs/hashes and extracted scalar
measurements are versioned. Decompress with `zlib.decompress(bytes, -15)`.
The public archives are unchanged and freely downloadable. CSV block order
can be nonchronological; step start/end are ordered by measured `Step_Time`.
Protocol completeness checks use recorded discharge start/end voltage and
C/3 current, never an SOH-based filter. Invalid observations are explicitly
listed in `excluded_characterizations.csv` and are not imputed into labels.

Every new SOH value is recomputed as:

```text
100 * max(Discharge_Capacity in characterization step 11)
    / max(Discharge_Capacity in that cell's pristine cycle-0 step 11)
```

Both measurements are at the same 50C chamber setting and C/3 protocol.
The same-cell reference is documented by protocol, not inferred from a
degraded initial observation or replaced by nominal capacity. Every row
retains the reference's capacity, cycle, source member and SHA256. No
interpolation, rescaling of healthy rows, invented history, or relabeling
of charge as discharge is used. Reference and discharge capacity remain
offline labels/metadata and never enter predictive features.

## Compatibility and other sources examined

The obtained LFP dataset is kept in
`ml/data/wheeler2025_discharge_measured.csv`, separately from the original
master. Shared chemistry and nominal capacity do not establish matching
discharge rate, operating temperature, sensor definitions, or reference
protocol. IR and measured cell temperatures are absent here; neither is
invented from chamber settings or EIS. The new inputs are only actual
C/3 charge capacity, charge duration, aging cycle count, and their observed
causal history. They are not interchangeable with original fast-charge
cycle measurements. Controlled charge and discharge capacities strongly
correlate; any low errors are specific to this characterization procedure.

Other public candidates were inspected via primary publisher pages:

| Source | Decision |
|---|---|
| [UConn-ILCC NMC/Gr](https://digitalcommons.lib.uconn.edu/reil_datasets/2/) | 44 Panasonic UR18650AA cells, stated 65% endpoint and CC BY 4.0, but different chemistry and protocol; not pooled or downloaded. |
| [UConn-ISU-ILCC LFP/Gr](https://digitalcommons.lib.uconn.edu/reil_datasets/1/) | Stated 80% endpoint; does not establish required 50-70% coverage. Not downloaded. |
| [Second-life LFP, Zenodo](https://zenodo.org/records/18630889) | 23 LongTTech cells with unknown prior degradation history; no documented measured BOL discharge reference was established. Not normalized to 100% or merged. |
| [Long-term sweat testing](https://doi.org/10.1038/s41597-025-05360-7) | LMO/LNO 66 Ah modules, unknown first-life history and limited reliable capacity tests; incompatible reference and operating domain. Not downloaded. |
| [UConn-MathWorks LFP second life](https://digitalcommons.lib.uconn.edu/reil_datasets/3/) | 1.2 Ah cells, large first/second-life raw archives. Potential future separate cohort; not claimed as obtained or verified for this extension. |

## Modeling and lifecycle semantics

Version 3 adapts the version-2 Ridge/XGBoost/CatBoost candidate search,
preserving the old implementation and bundles. Splits are battery-grouped,
stratified by the source's seven aging protocols: one train and one test
replicate per protocol, plus one validation replicate where available.
Seed 42; grouping uses IDs/protocols, never SOH or test errors. This tests
new cells under known protocols, not transfer to unseen protocols.
Train-only preprocessing and causal history are tested. Ridge's numeric
imputation is fitted on training features only; missing historical values
are never represented as additional measured observations. Trees use native
missing branches. Validation selects hyperparameters and model family;
test labels do not tune or stop fitting. Report MAE/RMSE in percentage
points overall, per battery, and for [50,60) and [60,70), including counts.
Absent coverage has null errors. All families are retained as diagnostics;
only the validation-selected family is served.

Primary-life capacity crossing at 80% does not establish second-life end
of service. Crossing between sparse characterizations is interval-censored;
an already-below-80% start is left-censored. No crossing cycle is interpolated.
Recording ends are censored follow-up, never failures. No application-specific
second-life endpoint is justified, so no second-life RUL target is trained.
The v3 API always returns `rul: null` and includes the limitation. Existing
v2 primary-life RUL is retained separately and is not presented as
second-life RUL. No reliable deployment accuracy or confidence interval is
claimed from the small new research cohort.

## Reproduction commands

Run at repository root with the installed Python environment. Network
acquisition requires network permission. The data-generation commands below
record the commands used; they fail closed if generated outputs already
exist. In this checkout, reuse the recorded CSVs and start at training with
a **new** run name, or verify the existing bundle with a **new** report
directory. Do not remove preserved outputs to rerun.

```powershell
python -m scripts.fetch_soh_measurements
python -m scripts.fetch_wheeler_characterizations --stride 400 --workers 4
python -m scripts.fetch_wheeler_characterizations --reaudit-cached
python -m scripts.build_measured_extension
python -m ml.pipeline_v3.train --output ml/artifacts/pipeline_v3/run-20261111-measured-v3.0.0 --iterations 500 --threads 4
python -m scripts.verify_measured_extension --bundle ml/artifacts/pipeline_v3/run-20261111-measured-v3.0.0 --output reports/soh_extension/verification
python -m pytest -q -p no:cacheprovider --basetemp reports/soh_extension/pytest_final
```

Frontend commands, from `frontend/`:

```powershell
npm.cmd test
npm.cmd run build
```

PowerShell's execution policy blocked `npm.ps1`; invoking the provided
`npm.cmd` wrapper completed normally without changing execution policy.
The build has the existing >500 kB bundle-size advisory. Initial test
run before model acquisition: 117 passed, 8 new bundle-dependent tests
skipped. Final post-training run: **125 passed, zero skipped**; frontend
**3/3 passed**, and production build passed. Final results are recorded in
`validation_results.json` and `pytest_final_results.xml`. Exact new API
parity passed for 80 held-out single records and seven held-out histories.
The original API also passed full parity for 18,512 single records and
21 histories; see `legacy_api_verification/parity.json`. All 131 preserved
original file hashes remain unchanged.

The initial downloader used four concurrent cells. To finish acquisition
sooner, six later cells were also cached using `--workers 6 --cells Cell6a
Cell6b Cell6c Cell7a Cell7b Cell7c`. This uses the same sampling rule and
measurements; it does not add observations to the fixed sample. Local
`--reaudit-cached` recomputes all summaries using the corrected step-time
ordering and verifies retained source SHA256s without another download.

To serve the separate research contract:

```powershell
$env:ECOCYCLE_V3_BUNDLE = 'ml/artifacts/pipeline_v3/run-20261111-measured-v3.0.0'
python -m uvicorn backend.main:app
```

`POST /v3/predict` requires `domain: "wheeler_C3_50C"`, `contract: "single"`
or `"history"`, and measured records with `QCharge`, `chargetime`, `cycle`
and, for history, `battery_id`. Histories need two real observations from
one battery. Targets, references, temperatures and engineered fields are
rejected. The existing frontend continues to use its v2 model; it does
not gain validated low-SOH coverage from this separate research cohort.
