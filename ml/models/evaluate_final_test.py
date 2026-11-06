"""
EcoCycle AI — Final Test Evaluation Module (Task 2L.3 Phase B)
Evaluates locked winning baseline models strictly on the quarantined Test partition.
No fitting, tuning, or refitting is performed.
"""
import numpy as np
import pandas as pd
from .evaluation import compute_regression_metrics

def evaluate_test_partition(model, X_test, y_test, metadata_df, target_name):
    """
    Generates test predictions and calculates MAE, RMSE, R2.
    Asserts no NaNs or Infs.
    """
    y_pred = model.predict(X_test)
    
    assert len(y_pred) == len(y_test), f"Length mismatch: {len(y_pred)} vs {len(y_test)}"
    assert not np.isnan(y_pred).any(), "NaN found in test predictions"
    assert not np.isinf(y_pred).any(), "Inf found in test predictions"
    
    metrics = compute_regression_metrics(y_test, y_pred)
    
    pred_df = pd.DataFrame({
        "battery_id": metadata_df["battery_id"].values,
        "cycle": metadata_df["cycle"].values,
        f"actual_{target_name.lower()}": y_test.values,
        f"pred_{target_name.lower()}": y_pred,
        "residual": y_test.values - y_pred
    })
    
    return metrics, pred_df
