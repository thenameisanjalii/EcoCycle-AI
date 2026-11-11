"""Separate legacy SOH labels and explicit, right-censored failure endpoints."""
import numpy as np
import pandas as pd


def failure_targets(data, threshold=80.0, confirmation=3):
    """Failure = cycle of Nth consecutive observed cycle with SOH < threshold.

    Cycles must differ by exactly one; gaps or an SOH >= threshold reset the run.
    Failure is dated at confirmation, never backdated. Post-event rows excluded.
    Nonfailures retain censor_cycle and lower-bound followup, with RUL = NaN.
    """
    if not 0 < threshold < 110 or confirmation < 1:
        raise ValueError("Invalid failure threshold or confirmation count.")
    if data.duplicated(["battery_id", "cycle"]).any():
        raise ValueError("Duplicate battery/cycle targets are ambiguous.")
    frames, trajectories = [], []
    for bid, group in data.groupby("battery_id", sort=False):
        g = group.sort_values("cycle").copy()
        run, previous, event = 0, None, None
        for row in g.itertuples():
            run = (run + 1 if previous is not None and row.cycle == previous + 1 else 1) if row.SOH < threshold else 0
            previous = row.cycle
            if run >= confirmation:
                event = float(row.cycle)
                break
        end = float(g.cycle.max())
        g["event_observed"] = event is not None
        g["event_cycle"] = event if event is not None else np.nan
        g["censor_cycle"] = end if event is None else np.nan
        g["followup_cycles"] = (event if event is not None else end) - g.cycle
        g["RUL_endpoint"] = event - g.cycle if event is not None else np.nan
        g["at_risk"] = g.cycle <= event if event is not None else True
        trajectories.append({"battery_id": bid, "event_observed": event is not None,
                             "event_cycle": event, "censor_cycle": end if event is None else None,
                             "recording_end": end})
        frames.append(g)
    return pd.concat(frames).sort_index(), pd.DataFrame(trajectories)
