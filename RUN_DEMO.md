# DriftGuard Live Demo Run Guide

This guide walks you through launching the DriftGuard platform and executing the full-stack configuration drift analysis flow.

## Startup Sequence (Three Terminals)

Open three separate terminal windows and run the following commands:

### Terminal 1: ML Inference Service
Start the ML inference engine on port `8080`:
```bash
cd /Users/disha/.gemini/antigravity-ide/scratch/DriftGuard-ml/deployment/driftguard_backend_bundle
python3 -m uvicorn driftguard_inference.app:app --host 127.0.0.1 --port 8080
```

### Terminal 2: Main Backend API
Start the FastAPI backend server on port `8000`:
```bash
cd /Users/disha/.gemini/antigravity-ide/scratch/DriftGuard-backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 3: Frontend Web App
Serve the static web dashboard on port `5500`:
```bash
cd /Users/disha/.gemini/antigravity-ide/scratch/DriftGuard-frontend
python3 -m http.server 5500
```

---

## Click-Path to Reproduce Demo

1. Open your web browser and navigate to: **`http://localhost:5500`**
2. **Log In**:
   - **Email**: `admin@driftguard.io`
   - **Password**: `admin123`
3. **Execute Scan**:
   - Click the glowing **`Run Git Compliance Scan`** button in the upper right.
   - Wait for the console logger modal to progress and complete (takes ~2 seconds).
4. **Verify Findings**:
   - The **Compliance Status** summary will update.
   - Click the **`Risk Log`** tab or click on a finding in the **`Dashboard`** tab to inspect the details.
   - Click on the new finding to open the modal and read the **DriftGuard LLM Compliance Analyzer** rationale generated dynamically by the model.
5. **Role Restrictions (Optional)**:
   - Log out, and log back in as a viewer: `viewer@driftguard.io` / `viewer123`.
   - The `Run Git Compliance Scan` button will be disabled, and the `Revert Configurations (Fix)` button inside findings will be greyed out.
