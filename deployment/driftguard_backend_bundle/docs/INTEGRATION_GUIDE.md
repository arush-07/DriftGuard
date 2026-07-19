# DriftGuard Integration Guide

## Install

Open a terminal inside the backend bundle directory:

    pip install -r requirements.txt

## Run the API

    uvicorn driftguard_inference.app:app --host 0.0.0.0 --port 8000

## Health check

Open:

    http://localhost:8000/health

Or run:

    curl http://localhost:8000/health

## Prediction request

Windows Command Prompt:

    curl -X POST http://localhost:8000/predict ^
      -H "Content-Type: application/json" ^
      --data @examples/prediction_request.json

PowerShell:

    Invoke-RestMethod `
      -Uri "http://localhost:8000/predict" `
      -Method Post `
      -ContentType "application/json" `
      -InFile "examples/prediction_request.json"

## Direct Python use

    from driftguard_inference import DriftGuardEngine

    engine = DriftGuardEngine()

    response = engine.predict_changes(
        [
            {
                "field_path": "tls.enabled",
                "old_value": "true",
                "new_value": "false",
                "configuration_type": "yaml",
                "parser_mode": "structured",
                "operation": "modified",
                "file_path": "config.yaml",
                "commit_message": "disable tls",
            }
        ]
    )

    print(response)

## Input fields

Operational fields:

- `field_path`
- `old_value`
- `new_value`
- `configuration_type`
- `parser_mode`
- `operation`
- `file_path`
- `commit_message`

Optional identifiers:

- `diff_id`
- `repository`
- `commit_hash`

## Output interpretation

- `safety_hybrid_prediction`: final categorical risk class
- `safety_hybrid_confidence`: confidence of the hybrid prediction
- `change_risk_score`: field-level risk score from 0 to 100
- `uncertainty_score`: uncertainty in the probability distribution
- `drift_band`: stable, watch, concerning, high, or critical
- `deterministic_rule_ids`: matched security rules
- `decision_source`: source of the final decision
- `decision_reason`: reason for model or rule intervention
- `commit_summary`: aggregate risk for submitted changes

## Deployment recommendations

- Protect the endpoint using authentication.
- Do not record raw secrets in application logs.
- Introduce request-size limits.
- Send high and critical predictions for human review.
- Store model and configuration hashes with every deployment.
- Do not alter frozen thresholds using final-test results.
