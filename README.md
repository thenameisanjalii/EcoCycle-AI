# EcoCycle AI 🔋♻️

**EcoCycle AI** is an intelligent AI/ML platform engineered for EV Battery Second-Life Assessment, State of Health (SOH) estimation, Remaining Useful Life (RUL) prediction, and circular economy recycling optimization.

## Repository Architecture

```
EcoCycle-AI/
├── configs/          # Experiment, training, data, and model YAML configurations
├── data/             # Raw, interim, processed, and feature datasets (git-ignored)
├── notebooks/        # Jupyter notebooks for exploratory data analysis and validation
├── src/              # Core modular pipeline source code
│   ├── data/
│   ├── preprocessing/
│   ├── features/
│   ├── models/       # Baseline, Classical ML, and Deep Learning models
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── decision/     # Second-life decision matrix logic
├── artifacts/        # Serialized model checkpoints, preprocessors, and metadata
├── experiments/      # Experiment tracking logs and registries
├── backend/          # FastAPI backend services and schemas
├── frontend/         # Web dashboard UI
├── tests/            # Unit, integration, and validation tests
├── docs/             # Technical architecture, dataset, and API documentation
└── reports/          # Data audit, experimental, and final comparison reports
```

## Setup & Environment

1. Clone or navigate to the repository directory:
   ```bash
   cd EcoCycle-AI
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and adjust configuration parameters:
   ```bash
   cp .env.example .env
   ```

## Workflow Progression

- **Task 1**: Project Architecture & Folder Scaffolding (Completed)
- **Task 2**: Dataset Audit & Verification (Pending)
- **Task 3**: Baseline Models & Data Preprocessing
- **Task 4**: Feature Engineering & ML Pipeline
- **Task 5**: Deep Learning Models (SOH & RUL)
- **Task 6**: API & Backend Integration
- **Task 7**: Frontend UI Dashboard

## Run the Application

The current application is a FastAPI backend. Run the following commands from the
project root on Windows PowerShell:

```powershell
cd "D:\MCA\Sem 5\Minor Project\EcoCycle-AI\EcoCycle-AI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If model loading reports that CatBoost is missing, install it inside the active
virtual environment:

```powershell
pip install catboost
```

Start the API:

```powershell
python -m uvicorn backend.app.api.main:app --reload
```

Open the interactive API documentation at <http://127.0.0.1:8000/docs>.
The main endpoints are:

| Method | Endpoint           | Purpose                                          |
| ------ | ------------------ | ------------------------------------------------ |
| GET    | `/health`          | Check service and model availability             |
| GET    | `/model-info`      | View model and dataset provenance                |
| POST   | `/predict`         | Predict SOH and RUL for one record               |
| POST   | `/predict/batch`   | Predict SOH and RUL for multiple records         |
| POST   | `/decision/assess` | Return prediction and second-life recommendation |

The API must receive all 32 causal features. `battery_id` and `row_id` are
optional metadata fields. Do not send leakage fields such as `QDischarge`,
`max_cycle`, `final_cycle`, `terminal_cycle`, `total_cycles`, `SOH`, or `RUL`.

## Demonstration Scripts

Run the model inference demonstration:

```powershell
python scripts/demo_inference.py
```

Run the second-life decision demonstration:

```powershell
python scripts/demo_decision.py
```

Both scripts use synthetic telemetry and do not read the quarantined test set.

## Test Commands

Run the complete test suite. The API server does not need to be running because
the API tests use FastAPI `TestClient`:

```powershell
python -m pytest -q
```

Run all tests with names and individual results:

```powershell
python -m pytest -v
```

Run individual test files:

```powershell
python -m pytest tests/test_input_validation.py -v
python -m pytest tests/test_final_model_loading.py -v
python -m pytest tests/test_inference_contract.py -v
python -m pytest tests/test_api_integration.py -v
python -m pytest tests/test_decision_engine.py -v
python -m pytest tests/test_decision_api.py -v
```

Run one test or a group of tests by keyword:

```powershell
python -m pytest tests/test_api_integration.py::test_03_valid_prediction -v
python -m pytest -k leakage -v
```

## Sample Prediction Data

Use the following complete JSON objects with `POST /predict` or
`POST /decision/assess`. Every valid example contains all 32 required features.

### Scenario A: Healthy Battery

Expected general result: healthy SOH and usually `PRIMARY_OPERATION`.

```json
{
  "cycle": 50.0,
  "IR": 0.008,
  "QCharge": 1.075,
  "Tavg": 28.0,
  "Tmax": 29.5,
  "Tmin": 26.5,
  "chargetime": 43.0,
  "IR_is_zero": 0.0,
  "temp_sensor_fault": 0.0,
  "IR_lag1": 0.0079,
  "IR_delta": 0.0001,
  "QCharge_lag1": 1.076,
  "QCharge_delta": -0.001,
  "Tavg_lag1": 27.9,
  "Tavg_delta": 0.1,
  "chargetime_lag1": 43.1,
  "chargetime_delta": -0.1,
  "IR_accel": 0.0,
  "QCharge_accel": 0.0,
  "Tavg_accel": 0.0,
  "chargetime_accel": 0.0,
  "thermal_dissipation_rate": 0.069767,
  "charge_efficiency_proxy": 0.025,
  "resistance_growth_ratio": 1.012658,
  "IR_roll_mean_5": 0.00795,
  "IR_roll_std_5": 0.00004,
  "QCharge_roll_mean_5": 1.0755,
  "QCharge_roll_std_5": 0.0005,
  "Tavg_roll_mean_5": 27.95,
  "Tavg_roll_std_5": 0.1,
  "cum_capacity_fade_rate": 0.00005,
  "cum_resistance_growth_rate": 0.00001,
  "battery_id": 888,
  "row_id": "healthy_cell_cycle_50"
}
```

### Scenario B: Degraded Second-Life Candidate

Expected general result: degraded SOH and usually `SECOND_LIFE_CANDIDATE`.

```json
{
  "cycle": 550.0,
  "IR": 0.0125,
  "QCharge": 0.94,
  "Tavg": 32.0,
  "Tmax": 34.5,
  "Tmin": 29.5,
  "chargetime": 38.0,
  "IR_is_zero": 0.0,
  "temp_sensor_fault": 0.0,
  "IR_lag1": 0.0123,
  "IR_delta": 0.0002,
  "QCharge_lag1": 0.943,
  "QCharge_delta": -0.003,
  "Tavg_lag1": 31.8,
  "Tavg_delta": 0.2,
  "chargetime_lag1": 38.2,
  "chargetime_delta": -0.2,
  "IR_accel": 0.0,
  "QCharge_accel": 0.0,
  "Tavg_accel": 0.0,
  "chargetime_accel": 0.0,
  "thermal_dissipation_rate": 0.131579,
  "charge_efficiency_proxy": 0.024737,
  "resistance_growth_ratio": 1.01626,
  "IR_roll_mean_5": 0.0122,
  "IR_roll_std_5": 0.00015,
  "QCharge_roll_mean_5": 0.945,
  "QCharge_roll_std_5": 0.002,
  "Tavg_roll_mean_5": 31.7,
  "Tavg_roll_std_5": 0.25,
  "cum_capacity_fade_rate": 0.0002,
  "cum_resistance_growth_rate": 0.00004,
  "battery_id": 888,
  "row_id": "degraded_cell_cycle_550"
}
```

### Scenario C: Critical or End-of-Life Battery

Expected general result: critical SOH and usually `MATERIAL_RECYCLING`.

```json
{
  "cycle": 1150.0,
  "IR": 0.0195,
  "QCharge": 0.81,
  "Tavg": 36.5,
  "Tmax": 40.5,
  "Tmin": 33.0,
  "chargetime": 33.0,
  "IR_is_zero": 0.0,
  "temp_sensor_fault": 0.0,
  "IR_lag1": 0.019,
  "IR_delta": 0.0005,
  "QCharge_lag1": 0.816,
  "QCharge_delta": -0.006,
  "Tavg_lag1": 36.1,
  "Tavg_delta": 0.4,
  "chargetime_lag1": 33.5,
  "chargetime_delta": -0.5,
  "IR_accel": 0.0,
  "QCharge_accel": 0.0,
  "Tavg_accel": 0.0,
  "chargetime_accel": 0.0,
  "thermal_dissipation_rate": 0.227273,
  "charge_efficiency_proxy": 0.024545,
  "resistance_growth_ratio": 1.026316,
  "IR_roll_mean_5": 0.0188,
  "IR_roll_std_5": 0.0004,
  "QCharge_roll_mean_5": 0.82,
  "QCharge_roll_std_5": 0.005,
  "Tavg_roll_mean_5": 35.8,
  "Tavg_roll_std_5": 0.5,
  "cum_capacity_fade_rate": 0.00038,
  "cum_resistance_growth_rate": 0.00009,
  "battery_id": 888,
  "row_id": "critical_cell_cycle_1150"
}
```

### Scenario D: Invalid Physical Input

Start with any valid payload and change one field:

```json
{
  "cycle": 0.0
}
```

This should return HTTP `400`. Other invalid values include:

```json
{
  "QCharge": -1.0
}
```

```json
{
  "Tavg": 150.0
}
```

### Scenario E: Leakage Protection

Start with any valid payload and add one forbidden field:

```json
{
  "QDischarge": 1.05
}
```

This should return HTTP `422`. The following fields are also forbidden:
`max_cycle`, `final_cycle`, `terminal_cycle`, `total_cycles`, `SOH`, and `RUL`.

### Scenario F: Missing or Null Feature

Remove a required field such as `QCharge_lag1`, or set it to null:

```json
{
  "QCharge_lag1": null
}
```

This should return HTTP `400` or `422`, depending on whether Pydantic rejects
the request before the application validator runs.

## Optional Docker Run

If Docker Desktop is installed, run:

```powershell
docker compose up --build
```

Then open <http://127.0.0.1:8000/docs>. Stop the container with:

```powershell
docker compose down
```
