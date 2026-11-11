"""Shared train/inference cleaning. No battery identity or target enters X."""
import numpy as np
import pandas as pd

RAW = ["IR", "QCharge", "Tavg", "Tmax", "Tmin", "chargetime", "cycle"]
SENSORS = RAW[:-1]
FLAGS = ["IR_is_zero", "temp_sensor_fault", "chargetime_outlier"]
SINGLE_FEATURES = RAW + FLAGS + [f"{c}_missing" for c in SENSORS]
HISTORY_FEATURES = SINGLE_FEATURES + ["history_count", "observed_span", "cycle_gap"] + [
    f"{c}_{s}" for c in ["IR", "QCharge", "Tavg", "chargetime"]
    for s in ["lag1", "delta_per_cycle", "past_mean5", "past_std5"]
]
ALLOWED = set(RAW + ["battery_id", "row_id"])


def validate_raw(frame, history=False):
    """Reject physical impossibilities; repairable sensor faults remain flagged.

    Missing sensors are allowed, but QCharge and at least one other measurement
    must be observed. Zero IR and bad temperature channels are repairable.
    Charge time must be supplied in minutes; no guessed unit conversion.
    """
    d = frame.copy()
    unknown = set(d.columns) - ALLOWED
    if unknown:
        raise ValueError(f"Unsupported or leakage fields: {sorted(unknown)}")
    if d.empty:
        raise ValueError("At least one measurement record is required.")
    for col in RAW:
        if col not in d:
            d[col] = np.nan
        d[col] = pd.to_numeric(d[col], errors="raise").astype(float)
        if np.isinf(d[col]).any():
            raise ValueError(f"{col} must be finite.")
    if d.cycle.isna().any() or (d.cycle < 1).any() or (d.cycle > 100000).any():
        raise ValueError("cycle must be in [1, 100000].")
    for col, low, high in [("IR", 0, 10), ("QCharge", 0, 20), ("chargetime", 0, 100000)]:
        if ((d[col] < low) | (d[col] > high)).any():
            raise ValueError(f"Physical bound violation: {col} must be in [{low}, {high}].")
    if d.QCharge.isna().any() or (d.QCharge <= 0).any():
        raise ValueError("Positive measured QCharge is required (not discharge capacity).")
    if (d[SENSORS].notna().sum(axis=1) < 2).any():
        raise ValueError("At least two sensor measurements including QCharge are required.")
    if history:
        if "battery_id" not in d or d.battery_id.isna().any():
            raise ValueError("History requires battery_id on every record.")
        d["battery_id"] = d.battery_id.astype(str)
        if d.duplicated(["battery_id", "cycle"]).any():
            raise ValueError("Duplicate cycles within a battery are ambiguous and rejected.")
    return d


def sensor_values(d):
    x = d[SENSORS].copy()
    zero_ir = x.IR.eq(0)
    x.loc[x.IR <= 0, "IR"] = np.nan
    temp = ["Tmin", "Tavg", "Tmax"]
    bad = (~x[temp].ge(-30) | ~x[temp].le(100)).any(axis=1)
    bad |= (x.Tmin > x.Tavg) | (x.Tavg > x.Tmax)
    # A zero thermocouple reading is missing in this room-temperature protocol.
    bad |= x[temp].eq(0).any(axis=1)
    x.loc[bad, temp] = np.nan
    x.loc[x.chargetime <= 0, "chargetime"] = np.nan
    return x, zero_ir, bad


class MeasurementPreprocessor:
    """Train-only medians/bounds; history uses strictly previous observed rows.

    Absent historical lags/rolling statistics stay NaN (tree missing branches),
    never replaced by a fake previous cycle or an unavailable birth reference.
    """
    def fit(self, raw):
        d = validate_raw(raw)
        x, _, _ = sensor_values(d)
        self.time_upper = float(x.chargetime.quantile(.995))
        x.loc[x.chargetime > self.time_upper, "chargetime"] = np.nan
        self.medians = x.median().to_dict()
        if not np.isfinite(list(self.medians.values())).all():
            raise ValueError("Training data must include valid observations for every sensor.")
        self.support = {c: [float(x[c].min()), float(x[c].max())] for c in SENSORS}
        self.support["cycle"] = [float(d.cycle.min()), float(d.cycle.max())]
        return self

    def transform(self, raw, contract="single"):
        if contract not in {"single", "history"}:
            raise ValueError("contract must be single or history.")
        d = validate_raw(raw, history=contract == "history")
        if not hasattr(self, "medians"):
            raise ValueError("Fit the preprocessor on training batteries first.")
        # Internal position index is independent of client labels/index values.
        d = d.reset_index(drop=True)
        if contract == "history":
            d = d.sort_values(["battery_id", "cycle"], kind="stable")
        x, zero_ir, bad_temp = sensor_values(d)
        bad_time = (x.chargetime > self.time_upper) | x.chargetime.isna()
        x.loc[bad_time, "chargetime"] = np.nan
        missing = x.isna()
        observed = x.copy()
        if contract == "history":
            x = x.groupby(d.battery_id, sort=False).ffill()
        x = x.fillna(self.medians)
        x["cycle"] = d.cycle
        x["IR_is_zero"] = zero_ir.astype(int)
        x["temp_sensor_fault"] = bad_temp.astype(int)
        x["chargetime_outlier"] = bad_time.astype(int)
        for col in SENSORS:
            x[f"{col}_missing"] = missing[col].astype(int)
        if contract == "history":
            groups = d.groupby("battery_id", sort=False)
            x["history_count"] = groups.cumcount()  # count of preceding rows
            x["observed_span"] = d.cycle - groups.cycle.transform("first")
            x["cycle_gap"] = groups.cycle.diff()
            for col in ["IR", "QCharge", "Tavg", "chargetime"]:
                # Historical features come from real measurements, not imputed values.
                g = observed[col].groupby(d.battery_id, sort=False)
                lag = g.shift(1)
                x[f"{col}_lag1"] = lag
                x[f"{col}_delta_per_cycle"] = (observed[col] - lag) / x.cycle_gap
                x[f"{col}_past_mean5"] = g.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
                x[f"{col}_past_std5"] = g.transform(lambda s: s.shift(1).rolling(5, min_periods=2).std())
        features = HISTORY_FEATURES if contract == "history" else SINGLE_FEATURES
        return x[features].sort_index()

    def reliability(self, raw):
        d = validate_raw(raw)
        x, zero, bad = sensor_values(d)
        notes = []
        for i in range(len(d)):
            issues = []
            if bool(zero.iloc[i]): issues.append("zero_IR_sensor_fault")
            if bool(bad.iloc[i]): issues.append("temperature_sensor_fault_or_missing")
            if x.iloc[i].isna().any(): issues.append("missing_measurements_imputed")
            if pd.notna(d.chargetime.iloc[i]) and d.chargetime.iloc[i] > self.time_upper:
                issues.append("charge_time_outlier_minutes_required")
            for c, (lo, hi) in self.support.items():
                val = d[c].iloc[i]
                if pd.notna(val) and not lo <= val <= hi:
                    issues.append(f"{c}_outside_training_support")
            notes.append(issues)
        return notes
