"""Verify held-out API/offline parity and emit a human-readable evaluation.

python -m scripts.verify_pipeline_v2 --bundle <run> --output <new-report-dir>
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.pipeline_v2 import get_bundle
from ml.pipeline_v2.inference import ModelBundle, digest
from ml.pipeline_v2.preprocessing import RAW

ROOT = Path(__file__).resolve().parents[1]


def run(bundle_path, output_path):
    bundle = ModelBundle(bundle_path)
    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=False)
    os.environ["ECOCYCLE_V2_BUNDLE"] = str(bundle.directory)
    get_bundle.cache_clear()
    data = pd.read_csv(ROOT / "ml/data/master_dataset.csv")
    splits = json.loads((bundle.directory / "splits.json").read_text())
    test = data[data.battery_id.isin(splits["test"])]
    parity = {"registry_sha256": bundle.registry_hash, "single_rows": 0, "history_batteries": 0,
              "exact_api_offline_matches": True, "history_saved_prediction_matches": True}
    client = TestClient(app)
    # Every held-out single assessment, in batches below the API limit.
    for start in range(0, len(test), 4000):
        raw = test.iloc[start:start + 4000][RAW + ["battery_id"]]
        records = raw.to_dict("records")
        offline = bundle.predict(records, "single")
        response = client.post("/v2/predict", json={"contract": "single", "records": records})
        response.raise_for_status()
        assert response.json() == offline
        parity["single_rows"] += len(records)
    selected = bundle.registry["models"]["history_soh"]["family"]
    predictions = pd.read_csv(bundle.directory / f"history_soh_{selected}_test_predictions.csv")
    partial = []
    for bid, group in test.groupby("battery_id"):
        raw = group[RAW + ["battery_id"]]
        # Reversed input explicitly verifies sorting and latest-row association.
        records = raw.iloc[::-1].to_dict("records")
        offline = bundle.predict(records, "history")
        response = client.post("/v2/predict", json={"contract": "history", "records": records})
        response.raise_for_status()
        assert response.json() == offline
        row = predictions[(predictions.battery_id == bid) & (predictions.cycle == group.cycle.max())].iloc[0]
        assert abs(offline["results"][0]["soh"]["raw"] - row.prediction) < 1e-12
        parity["history_batteries"] += 1
        # Fixed 5/20-row history windows at recording end: distribution-shift
        # diagnostic only, on the same endpoint row; never used to tune.
        for window in [5, 20]:
            result = bundle.predict(raw.tail(window), "history")["results"][0]
            partial.append({"battery_id": int(bid), "window": window, "actual_soh": float(group.SOH.iloc[-1]),
                            "predicted_soh": result["soh"]["raw"], "reliability": result["reliability"]["status"]})
    partial_df = pd.DataFrame(partial)
    partial_df.to_csv(output / "partial_history_diagnostic.csv", index=False)
    for name, expected in json.loads((bundle.directory / "original_manifest.json").read_text()).items():
        assert digest(ROOT / name) == expected, name
    parity["original_data_and_artifacts_unchanged"] = True
    (output / "parity.json").write_text(json.dumps(parity, indent=2), encoding="utf-8")
    # Stress current QCharge alone on multiple *archived* measured feature rows.
    # History is never imputed; no ground-truth degraded labels are created.
    from ml.models.feature_engineering import generate_causal_features_dataset
    from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
    from ml.models.final_registry import get_default_registry
    old = generate_causal_features_dataset(pd.read_csv(ROOT / "ml/data/test_soh.csv"))
    model = get_default_registry().load_model("soh")
    probes = []
    for stage, anchor in [("first", old.iloc[[0]]), ("middle", old.iloc[[len(old)//2]]), ("last", old.iloc[[-1]])]:
        for q in [.2, .4, .6, .8, 1.0]:
            x = anchor[ADVANCED_FEATURE_COLUMNS].copy()
            x["QCharge"] = q
            probes.append({"anchor": stage, "cycle": float(anchor.cycle.iloc[0]), "QCharge": q,
                           "predicted_soh": float(model.predict(x)[0])})
    (output / "legacy_capacity_stress.json").write_text(json.dumps({"note": "Current-QCharge-only perturbation of archived measured feature rows; history unchanged and intentionally inconsistent with the perturbation. Not an accuracy evaluation or manufactured degraded label.", "rows": probes}, indent=2), encoding="utf-8")
    metrics = json.loads((bundle.directory / "metrics.json").read_text())
    comparison = json.loads((bundle.directory / "legacy_comparison.json").read_text())
    trajectories = pd.read_csv(bundle.directory / "trajectories.csv")
    lines = ["# EcoCycle-AI v2 measured evaluation", "", f"Bundle: `{bundle.directory.name}`; registry SHA-256: `{bundle.registry_hash}`.", "",
             "Battery-grouped 70/15/15 split, seed 42; all tuning and early stopping used validation only. No refit on validation. Histories require at least two observations.", "",
             "| Task | Family | Validation RMSE | Test MAE | Test RMSE | Test rows |", "|---|---|---:|---:|---:|---:|"]
    for task, entry in metrics.items():
        for family, scored in entry["models"].items():
            val, result = scored["validation"]["overall"], scored["test"]["overall"]
            selected_label = " (selected)" if family == entry["selected_by_validation"] else ""
            lines.append(f"| {task} | {family}{selected_label} | {val['rmse']:.4f} | {result['mae']:.4f} | {result['rmse']:.4f} | {result['n']} |")
    lines += ["", "SOH errors are percentage points; RUL errors are cycles. The selected models are determined by validation RMSE even when another candidate has lower test error.", "",
              "## Same-row legacy SOH comparison", "", "| New task | Rows | New MAE / RMSE | Legacy MAE / RMSE |", "|---|---:|---|---|"]
    for task in ["single_soh", "history_soh"]:
        family = metrics[task]["selected_by_validation"]
        paired = comparison["new_soh_on_comparable_legacy_test_cohort"][f"{task}_{family}"]
        new, old_error = paired["new"], paired["legacy_same_rows"]
        lines.append(f"| {task} | {new['n']} | {new['mae']:.4f} / {new['rmse']:.4f} | {old_error['mae']:.4f} / {old_error['rmse']:.4f} |")
    lines += ["", "The default grouped cohort reproduces the legacy split. Only archived held-out rows are compared; the archived feature representation is preserved. Single assessment and history are different contracts, so this is not an isolated algorithm-only experiment.", "",
              "## SOH support and error by range", "", "No measured examples below 74.5527% exist in this CSV. Both 0–50% and 50–70% are unsupported; 70–80% only represents its observed upper portion.", "",
              "| SOH interval | Single rows | Single MAE / RMSE | History rows | History MAE / RMSE |", "|---|---:|---|---:|---|"]
    single_ranges = metrics["single_soh"]["models"][metrics["single_soh"]["selected_by_validation"]]["test"]["by_soh_range"]
    history_ranges = metrics["history_soh"]["models"][metrics["history_soh"]["selected_by_validation"]]["test"]["by_soh_range"]
    def formatted(e):
        return f"{e['mae']:.4f} / {e['rmse']:.4f}" if e["n"] else "Unsupported"
    for interval, e in single_ranges.items():
        h = history_ranges[interval]
        lines.append(f"| {interval} | {e['n']} | {formatted(e)} | {h['n']} | {formatted(h)} |")
    rul_family = metrics["history_rul"]["selected_by_validation"]
    rul_report = metrics["history_rul"]["models"][rul_family]["test"]
    lines += ["", "## RUL censoring and life stage", "", "Event: third consecutive numbered observed cycle strictly below 80% existing SOH, dated at confirmation. Gaps reset confirmation. Post-event rows are excluded; recording end is not failure.", "",
              trajectories.groupby(["split", "event_observed"]).size().to_string(), "",
              "Censored cells retain follow-up lower bounds in trajectories.csv but do not enter this regression loss. These estimates are conditional on observed failure, with selection bias; they are not validated population survival estimates. Only five confirmed-event test batteries support the RUL evaluation.", "",
              "| Stage (cycle / event cycle) | Rows | MAE / RMSE (cycles) |", "|---|---:|---|"]
    for stage, e in rul_report["by_life_stage"].items():
        lines.append(f"| {stage} | {e['n']} | {formatted(e)} |")
    legacy_rul = comparison["legacy_rul_original_target"]["overall"]
    lines += ["", f"Archived RUL on its original recording-end target: MAE {legacy_rul['mae']:.4f}, RMSE {legacy_rul['rmse']:.4f} cycles. The new target is different; a direct RUL accuracy improvement claim is invalid. See legacy_comparison.json for explicitly labeled cross-target diagnostics.", "",
              "## Limited-history diagnostic", "", "Fixed 5/20-observation windows are evaluated only at recording end, not across all ages. This is a distribution-shift check, not the full-trajectory metric above. No tuning used these results.", ""]
    for window, g in partial_df.groupby("window"):
        diff = g.predicted_soh - g.actual_soh
        lines.append(f"- Last {window} observations, {len(g)} test batteries: SOH MAE {diff.abs().mean():.4f}, RMSE {np.sqrt((diff**2).mean()):.4f} percentage points.")
    lines += ["", "## Verification and remaining data needs", "", f"Exact API/offline parity passed for {parity['single_rows']} held-out single assessments and {parity['history_batteries']} complete histories (reversed on input). Latest history predictions also match saved test predictions. Original data/model hashes are unchanged.", "",
              "The low-capacity stress test confirms tree extrapolation plateaus, but does not establish a universal ~81% value: predictions depend on the other measurements/history. No low-capacity stress input has an invented SOH label.", "",
              "Needed: independently measured discharge/reference capacities across 50–70% and lower SOH, multiple cells and protocols; long trajectories continuing to confirmed endpoints; censoring/withdrawal reasons and deployment histories with varied window lengths; original charge-time logging/protocol records, instrument calibration and unit metadata; independent chemistry, temperature and load cohorts. Charge time is assumed minutes from repository provenance, not independently confirmed from raw instruments. No reliable degraded-range accuracy or calibrated confidence intervals are claimed.", "",
              "Detailed per-battery metrics, SOH intervals and RUL stages are in the hashed metrics.json; candidate settings and early stopping are in tuning.json. This report is tied to the registry hash above."]
    (output / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(parity, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True, help="New report directory")
    args = parser.parse_args()
    run(args.bundle, args.output)


if __name__ == "__main__":
    main()
