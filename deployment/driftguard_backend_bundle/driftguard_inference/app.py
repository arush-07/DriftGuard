
from fastapi import FastAPI

from .engine import DriftGuardEngine
from .schemas import (
    PredictionRequest,
    PredictionResponse,
)


app = FastAPI(
    title="DriftGuard Inference API",
    version="1.0.0",
    description=(
        "Configuration-drift risk classification "
        "and cumulative commit scoring."
    ),
)

engine = DriftGuardEngine()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "driftguard",
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(
    request: PredictionRequest,
):
    changes = [
        change.model_dump()
        for change in request.changes
    ]

    return engine.predict_changes(
        changes
    )
