"""Run: python -m ml.pipeline_v2.train --output ml/artifacts/pipeline_v2/<run>"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

from ml.preprocessing.split import get_battery_splits
from . import VERSION
from .preprocessing import RAW, SINGLE_FEATURES, HISTORY_FEATURES, MeasurementPreprocessor
from .targets import failure_targets

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False, default=lambda v: v.item()), encoding="utf-8")


def errors(y, pred):
    if not len(y):
        return {"n": 0, "mae": None, "rmse": None, "status": "unsupported_no_examples"}
    diff = np.asarray(y) - np.asarray(pred)
    return {"n": len(diff), "mae": float(np.abs(diff).mean()), "rmse": float(np.sqrt(np.mean(diff ** 2)))}


def metric_report(data, target, pred):
    d = data[["battery_id", "cycle", "SOH"]].copy()
    d["actual"] = data[target].to_numpy()
    d["prediction"] = np.asarray(pred, dtype=np.float64)
    result = {"overall": errors(d.actual, d.prediction), "per_battery": {}}
    for bid, g in d.groupby("battery_id"):
        result["per_battery"][str(bid)] = errors(g.actual, g.prediction)
    if target == "SOH":
        result["by_soh_range"] = {}
        for lo, hi in [(0, 50), (50, 70), (70, 80), (80, 90), (90, 100), (100, 110)]:
            g = d[(d.SOH >= lo) & (d.SOH < hi)]
            result["by_soh_range"][f"[{lo},{hi})"] = errors(g.actual, g.prediction)
    else:
        # Life stage is evaluation-only, derived from observed failure (never X).
        progress = data.cycle / data.event_cycle
        result["by_life_stage"] = {}
        for name, lo, hi in [("early", 0, .33), ("middle", .33, .66), ("late", .66, 1.01)]:
            g = d[(progress >= lo).to_numpy() & (progress < hi).to_numpy()]
            result["by_life_stage"][name] = errors(g.actual, g.prediction)
    result["macro_battery_mae"] = float(np.mean([v["mae"] for v in result["per_battery"].values()])) if len(d) else None
    return result, d


def audit(data, path):
    refs = data[data.cycle <= 50].groupby("battery_id").QDischarge.mean()
    reconstructed = data.QDischarge / data.battery_id.map(refs) * 100
    _, trajectories = failure_targets(data)
    temps = data[["Tmin", "Tavg", "Tmax"]]
    return {
        "dataset_sha256": sha256(path), "rows": len(data), "batteries": data.battery_id.nunique(),
        "soh_min": float(data.SOH.min()), "soh_max": float(data.SOH.max()),
        "soh_below70": int((data.SOH < 70).sum()),
        "soh_formula_max_abs_error": float((reconstructed - data.SOH).abs().max()),
        "legacy_rul_formula_max_abs_error": float((data.groupby("battery_id").cycle.transform("max") - data.cycle - data.RUL).abs().max()),
        "duplicate_battery_cycles": int(data.duplicated(["battery_id", "cycle"]).sum()),
        "zero_IR": int(data.IR.eq(0).sum()),
        "temperature_invalid_or_zero": int(((temps < -30).any(axis=1) | (temps > 100).any(axis=1) | temps.eq(0).any(axis=1) | (data.Tmin > data.Tavg) | (data.Tavg > data.Tmax)).sum()),
        "chargetime_quantiles": {str(q): float(data.chargetime.quantile(q)) for q in [0, .5, .95, .99, .995, .999, 1]},
        "chargetime_over60": int((data.chargetime > 60).sum()),
        "chargetime_extremes": data.nlargest(20, "chargetime")[["battery_id", "cycle", "chargetime"]].to_dict("records"),
        "charge_time_units": "Minutes per repository provenance. CSV alone cannot confirm units or distinguish rests from logging faults. No automatic conversion; >train q99.5 treated as missing and flagged.",
        "default_confirmed_failures": int(trajectories.event_observed.sum()),
        "default_censored_batteries": int((~trajectories.event_observed).sum()),
    }


def candidates(x, y, vx, vy, seed, iterations, threads):
    """Small predefined search; only validation labels select/stop models."""
    for alpha in [1., 100.]:
        model = make_pipeline(SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True), StandardScaler(), Ridge(alpha=alpha))
        model.fit(x, y)
        yield "ridge", {"alpha": alpha}, model, errors(vy, model.predict(vx))
    for depth in [4, 7]:
        model = XGBRegressor(n_estimators=iterations, max_depth=depth, learning_rate=.05,
                             objective="reg:squarederror", tree_method="hist", subsample=.85,
                             colsample_bytree=.9, reg_lambda=5., random_state=seed,
                             n_jobs=threads, early_stopping_rounds=35)
        model.fit(x, y, eval_set=[(vx, vy)], verbose=False)
        yield "xgboost", {"max_depth": depth, "best_iteration": int(model.best_iteration)}, model, errors(vy, model.predict(vx))
    for depth in [4, 7]:
        model = CatBoostRegressor(iterations=iterations, depth=depth, learning_rate=.05,
                                  loss_function="RMSE", l2_leaf_reg=5., random_seed=seed,
                                  thread_count=threads, allow_writing_files=False, verbose=False)
        model.fit(x, y, eval_set=(vx, vy), early_stopping_rounds=35, verbose=False)
        yield "catboost", {"depth": depth, "best_iteration": int(model.get_best_iteration())}, model, errors(vy, model.predict(vx))


def legacy_comparison(labeled, test_ids, output):
    """Use old processed features only on its held-out battery cohort.

    Never count legacy train/validation cells as comparable test cells.
    Existing RUL estimates are *not* comparable failure-RUL estimates.
    """
    from ml.models.feature_engineering import generate_causal_features_dataset
    from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS
    from ml.models.final_registry import get_default_registry
    original_test = pd.read_csv(ROOT / "ml/data/test_soh.csv")
    comparable_ids = sorted(set(test_ids) & set(original_test.battery_id.unique()))
    cohort = labeled[labeled.battery_id.isin(comparable_ids)].copy()
    old = generate_causal_features_dataset(original_test)
    # Reindex on keys to preserve old training representation without mixing rows.
    old = old.set_index(["battery_id", "cycle"])
    keys = pd.MultiIndex.from_frame(cohort[["battery_id", "cycle"]])
    available = keys.isin(old.index)
    cohort = cohort.loc[available]
    old = old.loc[pd.MultiIndex.from_frame(cohort[["battery_id", "cycle"]])].reset_index()
    result = {"comparable_test_batteries": comparable_ids,
              "excluded_new_test_batteries_seen_by_legacy": sorted(set(test_ids) - set(comparable_ids)),
              "legacy_feature_contract": "Archived processed 17 features extended by original 32-feature generator; assumes full recorded history.",
              "rul_target_comparability": "Legacy RUL predicts recording end, not confirmed failure. Same-endpoint accuracy improvement cannot be claimed."}
    reg = get_default_registry()
    for target, label in [("soh", "SOH"), ("rul", "RUL")]:
        pred = reg.load_model(target).predict(old[ADVANCED_FEATURE_COLUMNS])
        report, rows = metric_report(cohort, label, pred) if target == "soh" else ({"overall": errors(cohort.RUL, pred)}, None)
        result[f"legacy_{target}_original_target"] = report
        if rows is not None:
            rows.to_csv(output / "legacy_soh_predictions.csv", index=False)
        else:
            keep = cohort.event_observed & cohort.at_risk
            diag, _ = metric_report(cohort.loc[keep], "RUL_endpoint", pred[keep.to_numpy()])
            result["legacy_rul_against_new_endpoint_diagnostic_only"] = diag
    # Deliberately out-of-support probe; these are NOT measured degraded examples.
    base = old.iloc[[0]][ADVANCED_FEATURE_COLUMNS].copy()
    probes = []
    for q in [.2, .4, .6, .8, 1.0]:
        x = base.copy()
        x["QCharge"] = q
        probes.append({"QCharge": q, "predicted_soh": float(reg.load_model("soh").predict(x)[0])})
    result["legacy_low_capacity_probe"] = {"note": "Only QCharge changed on a fixed archived feature row; intentionally inconsistent history, diagnostic extrapolation only; no expected SOH supplied.", "rows": probes}
    return result


def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)  # Never overwrite an artifact run.
    dataset = Path(args.dataset)
    data = pd.read_csv(dataset)
    original_files = sorted((ROOT / "ml/data").glob("*.csv")) + sorted((ROOT / "ml/artifacts/models").rglob("*.joblib")) + sorted((ROOT / "ml/artifacts/preprocessors").glob("*.joblib")) + [ROOT / "configs/final_model_registry.json"]
    preserved = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in original_files}
    write_json(output / "original_manifest.json", preserved)
    write_json(output / "audit.json", audit(data, dataset))
    if data.duplicated(["battery_id", "cycle"]).any():
        raise ValueError("Resolve duplicate battery cycles explicitly before training.")
    splits = get_battery_splits(data, args.seed, args.train_fraction, args.validation_fraction)
    split_names = ["train", "validation", "test"]
    split_ids = {name: [int(b) for b in ids] for name, ids in zip(split_names, splits)}
    write_json(output / "splits.json", split_ids)
    labeled, trajectories = failure_targets(data, args.threshold, args.confirmation)
    trajectories["split"] = trajectories.battery_id.map({b: s for s, ids in split_ids.items() for b in ids})
    trajectories.to_csv(output / "trajectories.csv", index=False)
    raw = data[RAW + ["battery_id"]]
    preprocessor = MeasurementPreprocessor().fit(raw[data.battery_id.isin(splits[0])])
    joblib.dump(preprocessor, output / "preprocessor.joblib")
    write_json(output / "preprocessing.json", {"medians": preprocessor.medians, "time_upper_minutes": preprocessor.time_upper, "training_support": preprocessor.support})
    schema = {"single": SINGLE_FEATURES, "history": HISTORY_FEATURES,
              "raw": RAW, "missing_history": "NaN, never synthetic lag values", "version": VERSION,
              "units": {"IR": "ohms", "QCharge": "Ah (charge, not discharge)", "Tavg": "C", "Tmin": "C", "Tmax": "C", "chargetime": "minutes", "cycle": "operating cycle count"},
              "history_window": "Up to five strictly preceding supplied observations, per battery; deltas divided by actual cycle gap; no birth-reference feature."}
    write_json(output / "feature_schema.json", schema)
    write_json(output / "config.json", vars(args))
    dependencies = {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn", "xgboost", "catboost", "joblib", "fastapi", "pydantic", "uvicorn", "pytest", "httpx"]}
    write_json(output / "dependencies.json", {"python": platform.python_version(), "packages": dependencies})
    (output / "requirements-lock.txt").write_text("\n".join(f"{p}=={v}" for p, v in dependencies.items()) + "\n", encoding="utf-8")
    metrics, selected, tuning = {}, {}, {}
    for task, contract, target in [("single_soh", "single", "SOH"), ("history_soh", "history", "SOH"), ("history_rul", "history", "RUL_endpoint")]:
        print(f"Training {task}", flush=True)
        # Build each partition independently; cleaning state never crosses batteries.
        parts, feats = {}, {}
        for name, ids in split_ids.items():
            g = labeled[labeled.battery_id.isin(ids)]
            parts[name] = g
            feats[name] = preprocessor.transform(g[RAW + ["battery_id"]], contract)
            feats[name].index = g.index
            mask = pd.Series(True, index=g.index)
            if contract == "history":
                mask &= feats[name].history_count >= 1  # same >=2-row contract as API
            if target == "RUL_endpoint":
                mask &= g.event_observed & g.at_risk
            parts[name] = g.loc[mask]
            feats[name] = feats[name].loc[mask]
        if any(parts[s].empty for s in split_names):
            metrics[task] = {"status": "unavailable_insufficient_confirmed_failure_cohort"}
            continue
        best_by_family, tuning[task] = {}, []
        for family, params, model, val in candidates(feats["train"], parts["train"][target], feats["validation"], parts["validation"][target], args.seed, args.iterations, args.threads):
            tuning[task].append({"family": family, "parameters": params, "validation": val})
            if family not in best_by_family or val["rmse"] < best_by_family[family][0]["rmse"]:
                best_by_family[family] = (val, model, params)
            print(f"  {family} {params}: validation RMSE={val['rmse']:.4f}", flush=True)
        winner = min(best_by_family, key=lambda f: best_by_family[f][0]["rmse"])
        selected[task] = {"family": winner, "artifact": f"{task}.joblib", "target": target, "contract": contract,
                          "parameters": best_by_family[winner][2], "features": schema[contract]}
        estimator = best_by_family[winner][1]
        parameters = (estimator.named_steps["ridge"] if winner == "ridge" else estimator).get_params()
        selected[task]["estimator_parameters"] = {k: "NaN" if isinstance(v, float) and np.isnan(v) else v for k, v in parameters.items()}
        joblib.dump(best_by_family[winner][1], output / f"{task}.joblib")
        metrics[task] = {"selected_by_validation": winner, "models": {}}
        for family, (val, model, params) in best_by_family.items():
            model_metrics = {"validation": val}
            for part in ["validation", "test"]:
                pred = model.predict(feats[part])
                report, rows = metric_report(parts[part], target, pred)
                model_metrics[part] = report
                rows.to_csv(output / f"{task}_{family}_{part}_predictions.csv", index=False)
            metrics[task]["models"][family] = model_metrics
    write_json(output / "tuning.json", tuning)
    write_json(output / "metrics.json", metrics)
    comparison = legacy_comparison(labeled, split_ids["test"], output)
    # Explicit same keys/cohort for new SOH models and legacy model.
    legacy_scored = pd.read_csv(output / "legacy_soh_predictions.csv")[["battery_id", "cycle", "prediction"]].rename(columns={"prediction": "legacy_prediction"})
    comparison["new_soh_on_comparable_legacy_test_cohort"] = {}
    for task in ["single_soh", "history_soh"]:
        for family in metrics[task]["models"]:
            scored = pd.read_csv(output / f"{task}_{family}_test_predictions.csv").merge(legacy_scored, on=["battery_id", "cycle"])
            comparison["new_soh_on_comparable_legacy_test_cohort"][f"{task}_{family}"] = {
                "new": errors(scored.actual, scored.prediction), "legacy_same_rows": errors(scored.actual, scored.legacy_prediction)}
    write_json(output / "legacy_comparison.json", comparison)
    source_dir = output / "source"
    source_dir.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        shutil.copyfile(source, source_dir / source.name)
    shutil.copyfile(ROOT / "ml/preprocessing/split.py", source_dir / "split.py")
    shutil.copyfile(ROOT / "backend/routes/pipeline_v2.py", source_dir / "api.py")
    for file, digest in preserved.items():
        if sha256(ROOT / file) != digest:
            raise RuntimeError(f"Original artifact changed: {file}")
    registry = {"version": VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
                "dataset_sha256": sha256(dataset), "models": selected,
                "soh_definition": "Existing SOH = measured QDischarge / mean QDischarge at cycles <=50 *100; reference not a predictor.",
                "rul_endpoint": {"threshold_soh": args.threshold, "confirmation_consecutive_cycles": args.confirmation,
                                 "event_time": "Nth consecutive observed cycle below threshold; exact consecutive cycle numbers required; no backdating",
                                 "regression_cohort": "Confirmed events only; censored trajectories excluded from regression; selection-biased conditional estimate, not population survival."},
                "soh_training_range": [float(data.loc[data.battery_id.isin(splits[0]), "SOH"].min()), float(data.loc[data.battery_id.isin(splits[0]), "SOH"].max())],
                "unsupported": "No measured SOH below 70%; reliable 50-70% accuracy is unsupported.",
                "cohort_summary": trajectories.groupby(["split", "event_observed"]).size().rename("batteries").reset_index().to_dict("records"),
                "files": {str(p.relative_to(output)).replace("\\", "/"): sha256(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "registry.json", registry)
    (output / "registry.sha256").write_text(sha256(output / "registry.json") + "\n", encoding="ascii")
    print(f"Saved immutable run: {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(ROOT / "ml/data/master_dataset.csv"))
    parser.add_argument("--output", required=True, help="NEW directory; existing runs are never overwritten")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-fraction", type=float, default=.7)
    parser.add_argument("--validation-fraction", type=float, default=.15)
    parser.add_argument("--threshold", type=float, default=80.)
    parser.add_argument("--confirmation", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.iterations < 2 or args.threads < 1:
        parser.error("iterations >=2 and threads >=1 required")
    run(args)


if __name__ == "__main__":
    main()
