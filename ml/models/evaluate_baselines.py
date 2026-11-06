"""
EcoCycle AI — Baseline Model Evaluation Module (Task 2L.2)
Evaluates predictions against the Validation partition (16,606 rows, 21 batteries).
Computes MAE, RMSE, R2, and saves prediction records.
"""
import numpy as np
import pandas as pd
from .evaluation import compute_regression_metrics

def evaluate_models_on_validation(trained_models, X_val, y_val, df_val_metadata, target_name):
    """
    Generates predictions and evaluates MAE, RMSE, R2 on the Validation partition.
    Returns:
        metrics_dict: dict of model_name -> metrics
        predictions_dfs: dict of model_name -> prediction DataFrame
    """
    results = {}
    predictions_dfs = {}
    
    for name, model in trained_models.items():
        y_pred = model.predict(X_val)
        
        # Sanity checks
        assert not np.isnan(y_pred).any(), f"NaN found in predictions for {name}"
        assert not np.isinf(y_pred).any(), f"Inf found in predictions for {name}"
        assert len(y_pred) == len(y_val), f"Length mismatch: {len(y_pred)} vs {len(y_val)}"
        
        metrics = compute_regression_metrics(y_val, y_pred)
        results[name] = metrics
        
        pred_df = pd.DataFrame({
            "battery_id": df_val_metadata["battery_id"].values,
            "cycle": df_val_metadata["cycle"].values,
            f"actual_{target_name.lower()}": y_val.values,
            f"pred_{target_name.lower()}": y_pred,
            "residual": y_val.values - y_pred
        })
        predictions_dfs[name] = pred_df
        
    return results, predictions_dfs
