"""
EcoCycle AI — Model Evaluation Utilities
Computes MAE, RMSE, R2, sample counts, and battery-level aggregations.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def compute_regression_metrics(y_true, y_pred):
    """
    Computes standard regression performance metrics.
    
    Why MAE:
        Mean Absolute Error represents the expected physical deviation on an intuitive,
        linear scale (% SOH or cycles for RUL). It is robust and easily communicated to engineers.
        
    Why RMSE:
        Root Mean Squared Error penalizes large divergence quadratically. In battery health
        and end-of-life assessment, severe under-prediction or over-prediction poses critical
        safety risks (unexpected cell shutdown, thermal runaway) or economic losses.
        
    Why R2:
        Provides normalized proportion of target variance explained relative to the naive mean.
        
    Returns:
        dict: {MAE, RMSE, R2, sample_count}
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    
    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "sample_count": int(len(y_true))
    }

def evaluate_battery_level(df, y_pred, target_col):
    """
    Computes metrics grouped by battery_id to analyze cell-level generalization variance.
    """
    temp_df = df[["battery_id", target_col]].copy()
    temp_df["pred"] = y_pred
    
    results = []
    for bat_id, grp in temp_df.groupby("battery_id"):
        m = compute_regression_metrics(grp[target_col], grp["pred"])
        results.append({
            "battery_id": bat_id,
            "n_cycles": len(grp),
            "MAE": m["MAE"],
            "RMSE": m["RMSE"],
            "R2": m["R2"]
        })
    return pd.DataFrame(results)
