# Changed files

Branch: `improve-soh-rul-pipeline`. No push. Original data/model hashes verified unchanged.

## Modified files

- `.env.example`
- `.gitignore`
- `README.md`
- `backend/main.py`
- `backend/routes/prediction.py`
- `backend/schemas/prediction_schema.py`
- `backend/schemas/telemetry.py`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/types.ts`
- `frontend/src/utils/validation.ts`
- `ml/models/input_validation.py`
- `ml/preprocessing/split.py`
- `pyproject.toml`
- `requirements.txt`

## New implementation, tests, documentation and examples

- `backend/routes/pipeline_v2.py`
- `docs/soh-rul-pipeline-v2.md`
- `examples/pipeline_v2/README.md`
- `examples/pipeline_v2/history.csv`
- `examples/pipeline_v2/single.csv`
- `frontend/src/utils/requestGate.ts`
- `frontend/tests/requestGate.test.mjs`
- `ml/pipeline_v2/__init__.py`
- `ml/pipeline_v2/inference.py`
- `ml/pipeline_v2/preprocessing.py`
- `ml/pipeline_v2/targets.py`
- `ml/pipeline_v2/train.py`
- `scripts/verify_pipeline_v2.py`
- `tests/test_pipeline_v2.py`

## New versioned artifacts

Registry SHA-256: `72b52eda2ff4c0e90226b6d46ad983c0c54567858a8cfdd23ea3f03ec53023be`.

- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/audit.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/config.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/dependencies.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/feature_schema.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul.joblib`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul_catboost_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul_catboost_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul_ridge_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul_ridge_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul_xgboost_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_rul_xgboost_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh.joblib`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh_catboost_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh_catboost_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh_ridge_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh_ridge_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh_xgboost_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/history_soh_xgboost_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/legacy_comparison.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/legacy_soh_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/metrics.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/original_manifest.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/preprocessing.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/preprocessor.joblib`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/registry.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/registry.sha256`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/requirements-lock.txt`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh.joblib`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh_catboost_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh_catboost_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh_ridge_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh_ridge_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh_xgboost_test_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/single_soh_xgboost_validation_predictions.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/__init__.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/api.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/inference.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/preprocessing.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/split.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/targets.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/source/train.py`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/splits.json`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/trajectories.csv`
- `ml/artifacts/pipeline_v2/run-20261111-v2.0.1/tuning.json`

## New evaluation and verification reports

- `reports/pipeline_v2/run-20261111-v2.0.1/example-single-prediction.json`
- `reports/pipeline_v2/run-20261111-v2.0.1/example-history-prediction.json`
- `reports/pipeline_v2/run-20261111-v2.0.1/changed-files.md`
- `reports/pipeline_v2/run-20261111-v2.0.1/evaluation.md`
- `reports/pipeline_v2/run-20261111-v2.0.1/legacy_capacity_stress.json`
- `reports/pipeline_v2/run-20261111-v2.0.1/parity.json`
- `reports/pipeline_v2/run-20261111-v2.0.1/partial_history_diagnostic.csv`
- `reports/pipeline_v2/run-20261111-v2.0.1/verification.md`

The pre-existing untracked frontend/.vite/ directory is excluded from this task inventory.
