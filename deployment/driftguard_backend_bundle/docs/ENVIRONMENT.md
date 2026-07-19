# DriftGuard Runtime Environment

## Supported installation choices

DriftGuard can run on either CPU or an NVIDIA CUDA 12.8 environment.

## CPU installation

```bash
python -m pip install -r requirements-cpu.txt
```

## NVIDIA CUDA 12.8 installation

```bash
python -m pip install -r requirements-cu128.txt
```

## Tested environment

- Python: 3.14
- PyTorch: 2.11.0+cu128
- TorchVision: 0.26.0+cu128
- CUDA runtime: 12.8
- FastAPI application import: passed
- DriftGuard engine import: passed
- Backend smoke test: passed

## Validate installation

```bash
python -c "import torch, transformers, sklearn, pandas, numpy, fastapi; print('Dependencies loaded')"
python -c "from driftguard_inference import DriftGuardEngine; print('Engine loaded')"
python -c "from driftguard_inference.app import app; print('API loaded')"
python -m pytest tests/test_smoke.py -v
```

## Start the API

```bash
uvicorn driftguard_inference.app:app --host 0.0.0.0 --port 8000
```

## API endpoints

- GET /health
- POST /predict

The complete model artifacts must remain inside the extracted models directory.
