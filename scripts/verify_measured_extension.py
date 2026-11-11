"""Full held-out measured API parity and self-contained evaluation report."""
import argparse
import json
import os
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.pipeline_v3 import get_bundle
from ml.pipeline_v2.inference import digest
from ml.pipeline_v3.inference import ModelBundle
from ml.pipeline_v3.preprocessing import RAW, DOMAIN

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = ModelBundle(args.bundle)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    dataset_path = Path(bundle.registry["dataset"])
    if not dataset_path.is_absolute():
        dataset_path = ROOT / dataset_path
    data = pd.read_csv(dataset_path)
    if digest(dataset_path) != bundle.registry["dataset_sha256"]:
        raise ValueError("Evaluation dataset hash mismatch")
    splits = json.loads((bundle.directory / "splits.json").read_text())
    test = data[data.battery_id.isin(splits["test"])]
    os.environ["ECOCYCLE_V3_BUNDLE"] = str(bundle.directory)
    get_bundle.cache_clear()
    parity = {"registry_sha256": bundle.registry_hash, "single_rows": 0, "history_batteries": 0,
              "exact_api_offline_matches": True, "history_saved_prediction_matches": True,
              "rul_always_unavailable": True}
    selected = bundle.registry["models"]["history_soh"]["family"]
    saved = pd.read_csv(bundle.directory / f"history_soh_{selected}_test_predictions.csv")
    with TestClient(app) as client:
        records = test[RAW + ["battery_id"]].to_dict("records")
        response = client.post("/v3/predict", json=dict(domain=DOMAIN, records=records))
        response.raise_for_status()
        expected = bundle.predict(records)
        assert response.json() == expected
        assert all(row["rul"] is None for row in expected["results"])
        parity["single_rows"] = len(records)
        for bid, group in test.groupby("battery_id"):
            records = group[RAW + ["battery_id"]].iloc[::-1].to_dict("records")
            expected = bundle.predict(records, "history")
            response = client.post("/v3/predict", json=dict(domain=DOMAIN, contract="history", records=records))
            response.raise_for_status()
            assert response.json() == expected
            assert expected["results"][0]["rul"] is None
            row = saved[(saved.battery_id == bid) & (saved.cycle == group.cycle.max())].iloc[0]
            assert abs(expected["results"][0]["soh"]["raw"] - row.prediction) < 1e-10
            parity["history_batteries"] += 1
    get_bundle.cache_clear()
    manifest = json.loads((ROOT / "reports/soh_extension/preservation_manifest.json").read_text())
    for name, expected_hash in manifest.items():
        assert digest(ROOT / name) == expected_hash, name
    parity["original_files_verified"] = len(manifest)
    parity["original_data_and_artifacts_unchanged"] = True
    (output / "parity.json").write_text(json.dumps(parity, indent=2), encoding="utf-8")
    metrics = json.loads((bundle.directory / "metrics.json").read_text())
    coverage = json.loads((bundle.directory / "coverage.json").read_text())
    acquisition = json.loads((ROOT / "reports/soh_extension/coverage.json").read_text())
    lines = ["# Measured discharge SOH extension evaluation", "",
        f"Bundle: `{bundle.directory.name}`, version `{bundle.registry['version']}`.",
        f"Registry SHA256: `{bundle.registry_hash}`.", "",
        "The original compatible master cohort is unchanged: 116,663 rows, 139 batteries, 74.5527-104.7925% SOH, zero observations in 50-60% or 60-70%. `master_dataset_extended.csv` is an exact preserved copy, not a claim of compatible low-SOH extension.", "",
        "The new measured-discharge data are kept separately in `ml/data/wheeler2025_discharge_measured.csv`. The 50C C/3 characterization protocol is incompatible with the original cycling telemetry. All results below apply only to this separate research cohort.", "",
        "SOH = measured C/3 discharge capacity / documented pristine cycle-0 C/3 discharge reference at the same 50C chamber setting * 100. The reference follows 25 documented wake-up cycles. No charge capacity, nominal rating, interpolated capacity, or degraded first observation substitutes for this discharge reference.", "",
        f"Acquisition: {acquisition['separate_wheeler_cohort']['rows']} valid measurements from {acquisition['separate_wheeler_cohort']['independent_batteries']} independent cells, {acquisition['excluded_rows']} excluded. Fixed sampling: cycle 0, every 400 cycles, final characterization. Measured SOH spans {data.SOH.min():.4f}-{data.SOH.max():.4f}%.", "",
        "## Grouped evaluation", "",
        "Cells are partitioned within the seven source aging protocols before inspecting labels: one train and one test cell per protocol, plus one validation cell for each three-replicate protocol. Seed 42. Cells never cross partitions. The protocols are shared across partitions, so this measures held-out cells under known laboratory protocols, not unseen protocols or deployment performance.", "",
        "Ridge scaling/imputation, feature support, and all estimator fitting use train cells only. Hyperparameters, early stopping and family selection use validation only. No refit on validation; test is evaluated only after selection. History uses only supplied, strictly preceding observations and actual cycle gaps. Missing history remains missing before train-only Ridge imputation; no unmeasured sensor is introduced.", "",
        "| Partition | Cells | Rows | SOH min/max | 50-60% rows/cells | 60-70% rows/cells |",
        "|---|---:|---:|---|---|---|"]
    for name, cohort in coverage.items():
        low, high = cohort["ranges"]["[50,60)"], cohort["ranges"]["[60,70)"]
        lines.append(f"| {name} | {cohort['independent_batteries']} | {cohort['rows']} | {cohort['soh_min']:.2f}/{cohort['soh_max']:.2f} | {low['rows']}/{low['independent_batteries']} | {high['rows']}/{high['independent_batteries']} |")
    lines += ["", "## Measured SOH errors", "", "Errors are percentage points; intervals are lower-inclusive and upper-exclusive. Independent cell counts are per interval and cannot be added across intervals. Empty intervals have null error, never a fabricated score.", "",
              "| Contract (selected family) | Test interval | Rows | Cells | MAE | RMSE |", "|---|---|---:|---:|---:|---:|"]
    def value(number):
        return "unsupported" if number is None else f"{number:.4f}"
    for contract in ["single", "history"]:
        task = metrics[f"{contract}_soh"]
        family = task["selected_by_validation"]
        report = task["models"][family]["test"]
        for name, score in [("overall", report["overall"]), *report["by_soh_range"].items()]:
            lines.append(f"| {contract} ({family}) | {name} | {score['n']} | {score['independent_batteries']} | {value(score['mae'])} | {value(score['rmse'])} |")
    lines += ["", "## Errors per independent test battery", "", "| Contract | Battery | Rows | MAE | RMSE |", "|---|---|---:|---:|---:|"]
    for contract in ["single", "history"]:
        task = metrics[f"{contract}_soh"]
        report = task["models"][task["selected_by_validation"]]["test"]
        for bid, score in report["per_battery"].items():
            lines.append(f"| {contract} | {bid} | {score['n']} | {value(score['mae'])} | {value(score['rmse'])} |")
    lines += ["", "## Primary and second life", "",
        "An observed SOH below 80% indicates crossing a conventional primary-life capacity threshold; it does not imply zero useful second-life service. With sparse characterization, the primary crossing is interval-censored between observations (or left-censored for an already-degraded start), never interpolated or assigned a fabricated exact cycle. Noncrossing observations are right-censored.", "",
        "No application-specific second-life service endpoint is established by this data. No second-life RUL estimator is trained, and API RUL is always null. Recorded ends are retained as censored follow-up with endpoint unknown. `trajectories.csv` explicitly retains these states. Choosing an arbitrary 60% endpoint would not establish service failure.", "",
        "## Verification and limitations", "",
        f"Exact API/offline parity passed for all {parity['single_rows']} held-out single records and all {parity['history_batteries']} held-out histories, reversed on input. Latest history predictions also match saved test predictions. {len(manifest)} original file hashes verified unchanged.", "",
        "This is a small, sparse, single-laboratory research evaluation, with seven independent test cells. Charge and discharge capacity are strongly related during this controlled characterization; the reported errors are not proof of field accuracy, calibrated uncertainty, safety, or transfer to other protocols. Aging chamber temperature is controlled at 50C, but cell temperature was not measured. No IR or temperature channels are invented. Existing source licensing was not independently revalidated; original data are retained without relicensing. The new source explicitly states CC BY 4.0 in dataset V2 metadata and README. Source attribution, acquisition and exclusions are documented in `reports/soh_extension/README.md`.", "",
        "All candidate validation/test metrics, per-battery errors and range errors are retained in the immutable bundle. No change to the existing frontend default or v2 bundle is made: its 50-70% accuracy remains unsupported. The new `/v3/predict` API requires explicit `domain: wheeler_C3_50C` and is a separate opt-in research contract.", ""]
    (output / "evaluation.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(parity, indent=2))


if __name__ == "__main__":
    main()
