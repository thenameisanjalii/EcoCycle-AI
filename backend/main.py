"""
EcoCycle AI — Main FastAPI Application Entrypoint
Task 2N — Production Inference API & Application Integration
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ml.models.input_validation import InputValidationError, DataLeakageError
from ml.models.final_registry import ModelRegistryError
from backend.routes.prediction import router
from backend.routes.decision import decision_router
from backend.routes.pipeline_v2 import router as pipeline_v2_router

app = FastAPI(
    title="EcoCycle AI — Battery Health Prediction & Lifecycle API",
    description=(
        "Production inference service for battery State of Health (SOH) and "
        "Remaining Useful Life (RUL) regression, leveraging 32 causal degradation "
        "features with strict anti-leakage protection."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(DataLeakageError)
async def data_leakage_exception_handler(request: Request, exc: DataLeakageError):
    """Custom handler converting DataLeakageError into HTTP 422 Unprocessable Entity."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_type": "DataLeakageError",
            "message": str(exc),
            "detail": "Data leakage violation: input contains forbidden training-only or future features."
        }
    )


@app.exception_handler(InputValidationError)
async def input_validation_exception_handler(request: Request, exc: InputValidationError):
    """Custom handler converting InputValidationError into HTTP 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_type": "InputValidationError",
            "message": str(exc),
            "detail": "Input validation failure: missing features, NaNs/Infs, or out-of-bounds sensor values."
        }
    )


@app.exception_handler(ModelRegistryError)
async def model_registry_exception_handler(request: Request, exc: ModelRegistryError):
    """Custom handler converting ModelRegistryError into HTTP 500 Internal Server Error."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_type": "ModelRegistryError",
            "message": str(exc),
            "detail": "Internal server error: model artifact or registry configuration failure."
        }
    )


# Root Endpoint
@app.middleware("http")
async def mark_legacy_targets(request, call_next):
    response = await call_next(request)
    if request.url.path in {"/predict", "/predict/batch", "/decision/assess"}:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = '</v2/predict>; rel="successor-version"'
        response.headers["Warning"] = '299 EcoCycle "Legacy RUL predicts recording end, not confirmed SOH failure."'
    return response


@app.get("/", tags=["General"])
def read_root():
    return {
        "service": "EcoCycle AI — Battery Health Prediction & Lifecycle API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "model_provenance": "/model-info",
        "inference_endpoints": {
            "single_record": "POST /predict",
            "batch_records": "POST /predict/batch",
            "decision_assessment": "POST /decision/assess"
        }
    }


# Include Routes
app.include_router(router)
app.include_router(decision_router)
app.include_router(pipeline_v2_router)
