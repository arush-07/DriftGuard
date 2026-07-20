# DriftGuard Backend Service

The core FastAPI backend service for **DriftGuard**, a configuration-drift and security-risk analysis platform.

## Features

- **Robust Database Schema**: Implements SQLAlchemy models for Users, Repositories, Scans, Change Records, Predictions, and Reviews.
- **Role-Based Access Control**: Pre-configured roles (`admin` and `viewer`) with granular restriction checks.
- **ML Integration**: Connects to the DriftGuard ML Inference Service to retrieve risk scores, classifications, and rule triggers.
- **CORS Configured**: Ready to interact with modern frontends.

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Start the API Server**:
   ```bash
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

## Running Tests

Run the test suite using pytest:
```bash
pytest -v
```
