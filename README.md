# EcoCycle-AI

The measurement-based SOH/RUL pipeline is now **v2**. Start with the
[v2 contracts, training/startup commands, definitions and limitations](docs/soh-rul-pipeline-v2.md)
and the [measured evaluation](reports/pipeline_v2/run-20261111-v2.0.1/evaluation.md).
The frontend uses `/v2/predict` and requires `ECOCYCLE_V2_BUNDLE` on the backend.
Original CSVs and models are preserved. The API contract below documents the
legacy compatibility routes: their RUL target is recording end, not failure.

## SOH, RUL, and Second-Life Prediction for EV Batteries

EcoCycle-AI is a machine-learning backend for assessing electric-vehicle battery
health and supporting second-life decisions. It predicts:

- **State of Health (SOH):** the battery's present health condition.
- **Remaining Useful Life (RUL):** the estimated number of usable cycles remaining.
- **Second-life suitability:** an operational interpretation of the SOH and RUL
  predictions for reuse and lifecycle planning.

The project is designed as an MCA minor project with a reproducible inference
pipeline, strict input validation, and protection against target and future-data
leakage.

## Architecture

The codebase is separated into two primary layers:

```text
EcoCycle-AI/
├── backend/
│   ├── main.py                 # FastAPI application and exception handlers
│   ├── routes/                 # Prediction and second-life API endpoints
│   ├── schemas/                # Strict Pydantic request/response models
│   └── services/               # Health interpretation and decision logic
├── ml/
│   ├── models/                 # Feature schemas, validation, inference, registry
│   ├── preprocessing/          # Causal feature preparation pipeline
│   └── artifacts/              # Saved joblib preprocessors and model artifacts
├── tests/                      # Unit and API tests
└── requirements.txt            # Python dependencies
```

### Backend

`backend/` exposes the FastAPI service and defines the public API contract.
Pydantic schemas validate request structure and types before inference. The
backend also returns model provenance and a deterministic battery-health
interpretation alongside SOH and RUL values.

### Machine-learning layer

`ml/` owns feature engineering, anti-leakage validation, model inference, and
the saved `joblib` artifacts used by the certified pipeline. This keeps model
logic independent from HTTP transport and makes the inference path reproducible.

## API Contract

### `POST /predict`

The smart prediction endpoint accepts a JSON object containing a chronological
`records` array. Each record contains the **19 raw historical request columns**:

1. `IR`
2. `QCharge`
3. `Tavg`
4. `Tmax`
5. `Tmin`
6. `chargetime`
7. `cycle`
8. `IR_is_zero`
9. `temp_sensor_fault`
10. `IR_lag1`
11. `IR_delta`
12. `QCharge_lag1`
13. `QCharge_delta`
14. `Tavg_lag1`
15. `Tavg_delta`
16. `chargetime_lag1`
17. `chargetime_delta`
18. `battery_id`
19. `row_id` (optional metadata)

The client does **not** send the model's engineered 32-feature vector. The
endpoint orders the supplied history, computes the causal rolling and cumulative
features internally, and uses the latest cycle for single-battery inference.
Only past and current observations are used; future values and target-derived
features are never used.

Inputs containing leakage fields such as `QDischarge`, `SOH`, `RUL`, or
`max_cycle` are rejected. Unknown fields are also rejected by the raw telemetry
schema. This prevents clients from bypassing the feature-generation pipeline or
accidentally providing target information.

### Other endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Verify service and model availability |
| `GET` | `/model-info` | Return model registry and dataset provenance |
| `POST` | `/predict` | Generate SOH and RUL from historical telemetry |
| `POST` | `/predict/batch` | Score validated 32-feature records in batches |
| `POST` | `/decision/assess` | Return a second-life decision assessment |

Interactive OpenAPI documentation is available at
<http://127.0.0.1:8000/docs> when the server is running.

## Getting Started

Run these commands from the repository root.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the API server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run the test suite

```bash
pytest
```

The suite covers schemas, leakage protection, causal preprocessing, censoring,
model integrity, offline/API parity and legacy API behavior. The frontend also
has request-race regression checks (`npm.cmd --prefix frontend test`).

## Example `/predict` Request

```json
{
  "records": [
    {
      "IR": 0.008,
      "QCharge": 1.075,
      "Tavg": 28.0,
      "Tmax": 29.5,
      "Tmin": 26.5,
      "chargetime": 43.0,
      "cycle": 50.0,
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
      "battery_id": "B0001",
      "row_id": "sample-50"
    }
  ]
}
```

The response includes raw and display-safe SOH/RUL values, units, model
provenance, preserved metadata, and the battery-health interpretation.

## Frontend dashboard

The `frontend/` directory contains the React + Vite presentation dashboard for
the API. It provides a responsive academic dashboard with:

- a persistent navigation sidebar for overview, prediction, analytics, and API health;
- editable multi-record raw telemetry input with CSV/JSON import and sample data;
- client-side validation, record sorting, leakage-field rejection, and the 5,000-record limit;
- latest-cycle SOH/RUL cards using the complete submitted history;
- Recharts-based telemetry and lag/delta degradation views; and
- `/health` model availability and pipeline-version monitoring.

The frontend deliberately calls only `POST /predict` for raw telemetry. The
advanced `/decision/assess` endpoint is not called because it expects engineered
32-feature input; the dashboard uses the interpretation returned by `/predict`.

### Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

For PowerShell, the environment-file command is:

```powershell
Copy-Item .env.example .env
```

The default `.env` value is `VITE_API_BASE_URL=http://localhost:8000`.
Start the backend separately with `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`.
The frontend production build is verified with `npm run build`.

### Frontend structure

```text
frontend/
├── src/
│   ├── services/api.ts       # fetch wrapper for /predict and /health
│   ├── utils/parser.ts       # CSV/JSON upload parsing
│   ├── utils/validation.ts   # raw contract, leakage, and limit validation
│   ├── types.ts              # telemetry and response types
│   ├── App.tsx               # dashboard views and modular UI components
│   └── index.css             # Tailwind theme and global styles
├── .env.example
├── package.json
└── vite.config.ts
```

### Backend integration verification

1. Start FastAPI and open `http://localhost:8000/health`; confirm `status` is
   `healthy` and both model flags are `true`.
2. Start the frontend and use **Use sample data**, then **Run prediction**.
3. Confirm the request in the browser Network panel is `POST /predict` with
   `{ "records": [...] }`, sorted by `cycle`, and contains only raw telemetry
   fields (no engineered 32-feature columns or target leakage fields).
4. Confirm the response populates SOH, RUL, metadata, interpretation, and model
   provenance, while charts continue to reflect the submitted history.
