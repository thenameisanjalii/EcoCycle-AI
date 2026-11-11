"""Adapt v2's validation-selected model search to a separate measured protocol.

python -m ml.pipeline_v3.train --output ml/artifacts/pipeline_v3/<new-run>
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil

import joblib
import numpy as np
import pandas as pd

from ml.pipeline_v2.train import candidates, errors, sha256, write_json
from scripts.build_measured_extension import validate_discharge_labels, coverage
from . import VERSION
from .preprocessing import DOMAIN, RAW, SINGLE_FEATURES, HISTORY_FEATURES, MeasurementPreprocessor

ROOT = Path(__file__).resolve().parents[2]


def grouped_protocol_splits(data, seed=42):
    """One independently held-out cell per test protocol, set before labels.

    Three replicates: train/test/validation; the two-replicate protocol gets
    train/test. No SOH values, endpoints, or test errors influence allocation.
    """
    if data.groupby("battery_id").test_group.nunique().gt(1).any():
        raise ValueError("A battery cannot cross protocol groups")
    rng = np.random.RandomState(seed)
    result = {"train": [], "validation": [], "test": []}
    for _, group in data[["battery_id", "test_group"]].drop_duplicates().groupby("test_group", sort=True):
        ids = rng.permutation(sorted(group.battery_id))
        if len(ids) not in {2, 3}:
            raise ValueError("Expected two or three independent cells per source protocol")
        result["train"].append(str(ids[0]))
        result["test"].append(str(ids[1]))
        if len(ids) == 3:
            result["validation"].append(str(ids[2]))
    return result


def metric_report(data, predictions):
    rows = data[["battery_id", "cycle", "SOH"]].copy()
    rows["actual"] = data.SOH
    rows["prediction"] = np.asarray(predictions)
    def score(group):
        return {**errors(group.actual, group.prediction), "independent_batteries": group.battery_id.nunique()}
    result = {"overall": score(rows), "per_battery": {str(b): score(g) for b, g in rows.groupby("battery_id")},
        "by_soh_range": {f"[{low},{high})": score(rows[(rows.SOH >= low) & (rows.SOH < high)])
            for low, high in [(0, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 110)]}}
    result["macro_battery_mae"] = float(np.mean([v["mae"] for v in result["per_battery"].values()])) if len(rows) else None
    return result, rows


def life_trajectories(data):
    """Primary-life crossing is interval/left censored; second life unmodeled.

    Sparse characterizations cannot establish three consecutive cycle events.
    No arbitrary lower SOH threshold is supplied as a second-life service end.
    """
    rows = []
    for bid, group in data.groupby("battery_id"):
        group = group.sort_values("cycle")
        below = group[group.SOH < 80]
        first = None if below.empty else int(below.cycle.iloc[0])
        before = group[group.cycle < first] if first is not None else group
        lower = int(before.cycle.iloc[-1]) if not before.empty else None
        rows.append(dict(battery_id=bid,
            primary_life_crossing_status="right_censored" if first is None else "left_censored" if lower is None else "interval_censored",
            primary_crossing_lower_cycle=lower, primary_crossing_upper_cycle=first,
            recording_end_cycle=int(group.cycle.max()), post_primary_observed_rows=len(below),
            second_life_endpoint_soh=None, second_life_event_observed=False,
            second_life_status="endpoint_undefined_followup_right_censored", second_life_rul=None))
    return pd.DataFrame(rows)


def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    data = pd.read_csv(args.dataset)
    validate_discharge_labels(data)
    if set(data.protocol) != {DOMAIN} or set(data.source_doi) != {"10.57745/OLBXKT"}:
        raise ValueError("Incompatible data must be evaluated in separate pipelines")
    if set(data.chemistry) != {"LFP/graphite"} or not data.nominal_capacity_Ah.eq(1.1).all():
        raise ValueError("Unverified cell chemistry/capacity")
    if set(data.license) != {"CC-BY-4.0"} or data.source_sha256.duplicated().any():
        raise ValueError("Invalid provenance/license or duplicate source content")
    original = json.loads((ROOT / "reports/soh_extension/preservation_manifest.json").read_text())
    for name, digest in original.items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Original changed: {name}")
    write_json(output / "original_manifest.json", original)
    splits = grouped_protocol_splits(data, args.seed)
    write_json(output / "splits.json", splits)
    write_json(output / "coverage.json", {name: coverage(data[data.battery_id.isin(ids)]) for name, ids in splits.items()})
    trajectories = life_trajectories(data)
    trajectories["split"] = trajectories.battery_id.map({b: s for s, ids in splits.items() for b in ids})
    trajectories.to_csv(output / "trajectories.csv", index=False)
    preprocessor = MeasurementPreprocessor().fit(data[data.battery_id.isin(splits["train"])][RAW])
    joblib.dump(preprocessor, output / "preprocessor.joblib")
    write_json(output / "preprocessing.json", {"training_support": preprocessor.support,
        "scaling_and_imputation": "Ridge pipeline fitted only on train; trees native NaN handling; no invented historical observations"})
    write_json(output / "config.json", vars(args))
    packages = {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn", "xgboost", "catboost", "joblib", "fastapi", "pydantic", "pytest", "httpx"]}
    write_json(output / "dependencies.json", {"python": platform.python_version(), "packages": packages})
    (output / "requirements-lock.txt").write_text("\n".join(f"{p}=={v}" for p, v in packages.items()) + "\n")
    metrics, selected, tuning = {}, {}, {}
    for contract in ["single", "history"]:
        task = f"{contract}_soh"
        parts, features = {}, {}
        for split, ids in splits.items():
            part = data[data.battery_id.isin(ids)]
            x = preprocessor.transform(part[RAW + ["battery_id"]], contract)
            x.index = part.index
            mask = x.history_count >= 1 if contract == "history" else pd.Series(True, index=part.index)
            parts[split], features[split] = part.loc[mask], x.loc[mask]
        if any(part.empty for part in parts.values()):
            raise ValueError("Empty grouped evaluation partition")
        best, tuning[task] = {}, []
        for family, params, model, val in candidates(features["train"], parts["train"].SOH,
                features["validation"], parts["validation"].SOH, args.seed, args.iterations, args.threads):
            tuning[task].append({"family": family, "parameters": params, "validation": val})
            if family not in best or val["rmse"] < best[family][0]["rmse"]:
                best[family] = (val, model, params)
            print(task, family, params, val, flush=True)
        winner = min(best, key=lambda family: best[family][0]["rmse"])
        joblib.dump(best[winner][1], output / f"{task}.joblib")
        selected[task] = {"family": winner, "contract": contract, "target": "SOH", "artifact": f"{task}.joblib",
                          "features": SINGLE_FEATURES if contract == "single" else HISTORY_FEATURES}
        metrics[task] = {"selected_by_validation": winner, "models": {}}
        for family, (_, model, _) in best.items():
            metrics[task]["models"][family] = {}
            for split in ["validation", "test"]:
                scored, rows = metric_report(parts[split], model.predict(features[split]))
                metrics[task]["models"][family][split] = scored
                rows.to_csv(output / f"{task}_{family}_{split}_predictions.csv", index=False)
    metrics["second_life_rul"] = {"status": "unavailable_no_justified_service_endpoint", "trained": False}
    write_json(output / "metrics.json", metrics)
    write_json(output / "tuning.json", tuning)
    source = output / "source"
    source.mkdir()
    for file in Path(__file__).parent.glob("*.py"):
        shutil.copyfile(file, source / file.name)
    for file in [ROOT / "scripts/build_measured_extension.py", ROOT / "scripts/fetch_wheeler_characterizations.py",
                 ROOT / "ml/pipeline_v2/train.py", ROOT / "backend/routes/pipeline_v3.py"]:
        shutil.copyfile(file, source / ("v2_train.py" if file.parent.name == "pipeline_v2" else file.name))
    train = data[data.battery_id.isin(splits["train"])]
    dataset_path = Path(args.dataset).resolve()
    dataset_record = dataset_path.relative_to(ROOT).as_posix() if dataset_path.is_relative_to(ROOT) else str(dataset_path)
    registry = {"version": VERSION, "domain": DOMAIN, "dataset": dataset_record,
        "dataset_sha256": sha256(args.dataset), "models": selected,
        "soh_definition": "100 * measured C/3 discharge Ah / same cell's documented pristine cycle-0 C/3 discharge Ah at 50C; charge capacity is never the label or denominator.",
        "soh_training_range": [float(train.SOH.min()), float(train.SOH.max())],
        "rul_endpoint": {"status": "unavailable", "primary_life": "80% crossing only, interval-censored between observed characterizations",
                         "second_life": "No justified application-specific endpoint. Follow-up is censored; no RUL regression trained."},
        "unsupported": "Research cohort only: 20 independent cells, sparse 400-cycle sampling at 50C. Measured range errors are not reliable deployment accuracy. Not validated for Severson telemetry or other chemistries/protocols.",
        "units": {"QCharge": "Ah, C/3 characterization step 13", "chargetime": "minutes, step 13 duration / 60", "cycle": "actual ageing cycles, pristine reference cycle 0"},
        "files": {p.relative_to(output).as_posix(): sha256(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "registry.json", registry)
    (output / "registry.sha256").write_text(sha256(output / "registry.json") + "\n")
    for name, digest in original.items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Original changed: {name}")
    print("Saved immutable measured run", output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(ROOT / "ml/data/wheeler2025_discharge_measured.csv"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.iterations < 2 or args.threads < 1:
        parser.error("iterations >=2 and threads >=1 required")
    run(args)


if __name__ == "__main__":
    main()
