# DriftGuard Backend Handoff

## Repository

- Repository: https://github.com/arush-07/DriftGuard
- Branch: ml
- Release tag: v1.0.0-ml
- Release asset: driftguard_backend_bundle.zip

## Required downloads

The ml branch contains the source code, notebooks, configurations, schemas, documentation, tests and inference package.

The trained model files are distributed through the GitHub Release ZIP because the Transformer weights are too large for normal Git.

The backend engineer must download:

- driftguard_backend_bundle.zip
- driftguard_backend_bundle.sha256
- BACKEND_BUNDLE_MANIFEST.json

## Included models

- TF-IDF text baseline classifier
- Structured ExtraTrees classifier
- CodeBERTa Transformer classifier
- Frozen tokenizer and Transformer configuration
- Deterministic hybrid security rules
- Drift scoring and cumulative-pressure engine

## CPU installation

Run:

python -m pip install -r requirements-cpu.txt

## NVIDIA CUDA 12.8 installation

Run:

python -m pip install -r requirements-cu128.txt

## Start the API

Run from inside the extracted bundle directory:

uvicorn driftguard_inference.app:app --host 0.0.0.0 --port 8000

## Endpoints

- GET /health
- POST /predict

## Test the installation

python -c "from driftguard_inference import DriftGuardEngine; print('Engine loaded')"

python -c "from driftguard_inference.app import app; print('API loaded')"

python -m pytest tests/test_smoke.py -v

## Important files

- driftguard_inference/engine.py
- driftguard_inference/app.py
- driftguard_inference/schemas.py
- configs/final_system_manifest.json
- docs/MODEL_CARD.md
- docs/INTEGRATION_GUIDE.md
- docs/ENVIRONMENT.md
- docs/FINAL_TEST_METRICS.json
- examples/prediction_request.json
- tests/test_smoke.py

## Integrity verification

On Windows PowerShell:

Get-FileHash .\driftguard_backend_bundle.zip -Algorithm SHA256

Compare the result with driftguard_backend_bundle.sha256.

## Production warning

High and critical predictions require human review.

The system must not be used as an autonomous exploitability, compliance or deployment-blocking authority without independent validation.
