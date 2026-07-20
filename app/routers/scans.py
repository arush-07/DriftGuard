from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import httpx
import logging

from ..database import get_db
from .. import models, schemas, auth
from ..services.ml_client import ml_client

logger = logging.getLogger("driftguard.scans")
router = APIRouter()

def get_utc_now():
    return datetime.now(timezone.utc)

async def run_scan_prediction(scan_id: str, changes_input: List[schemas.ConfigurationChangeInput], db_session: Session):
    # Retrieve scan
    scan = db_session.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        return

    try:
        scan.status = "processing"
        db_session.commit()

        # Map to prediction request changes
        ml_changes = []
        change_records_map = {}

        for ch in changes_input:
            # Store in DB first (redacted values)
            old_redacted = ml_client.redact_secrets(ch.old_value)
            new_redacted = ml_client.redact_secrets(ch.new_value)

            db_change = models.ChangeRecord(
                scan_id=scan.id,
                file_path=ch.file_path,
                configuration_type=ch.configuration_type,
                field_path=ch.field_path,
                old_value_redacted=old_redacted,
                new_value_redacted=new_redacted
            )
            db_session.add(db_change)
            db_session.commit()
            db_session.refresh(db_change)

            # Keep mapping
            change_records_map[ch.field_path + "@" + ch.file_path] = db_change.id

            # Prepare ML requestchange payload
            ml_changes.append({
                "diff_id": db_change.id,
                "repository": scan.repository.name,
                "commit_hash": scan.commit_sha or "runtime",
                "field_path": ch.field_path,
                "old_value": ch.old_value,
                "new_value": ch.new_value,
                "configuration_type": ch.configuration_type,
                "parser_mode": "structured",
                "operation": "modified",
                "file_path": ch.file_path,
                "commit_message": ch.commit_message or ""
            })

        # Send request to ML Inference Service
        ml_response = await ml_client.get_predictions(ml_changes)
        results = ml_response.get("results", [])

        high_count = 0
        critical_count = 0

        for res in results:
            diff_id = res.get("diff_id")
            # Fallback if diff_id not present or mismatched, find by field_path + file_path
            if not diff_id:
                fp = res.get("field_path", "")
                fpath = res.get("file_path", "")
                diff_id = change_records_map.get(fp + "@" + fpath)

            if not diff_id:
                # If still not found, skip or use first change
                continue

            drift_band = res.get("drift_band", "low")
            risk_level = drift_band  # e.g. stable, watch, concerning, high, critical
            predicted_class = res.get("safety_hybrid_prediction", "safe")
            confidence = res.get("safety_hybrid_confidence", 0.0)
            drift_score = res.get("change_risk_score", 0.0)
            rule_ids = res.get("deterministic_rule_ids", [])

            if risk_level.lower() == "high":
                high_count += 1
            elif risk_level.lower() == "critical":
                critical_count += 1

            # Persist prediction
            db_pred = models.Prediction(
                scan_id=scan.id,
                change_id=diff_id,
                predicted_class=predicted_class,
                risk_level=risk_level,
                confidence=confidence,
                drift_score=drift_score,
                rule_flags={"deterministic_rule_ids": rule_ids},
                raw_response=res,
                model_version=res.get("model_version", "v1.0.0-ml"),
                requires_review=risk_level.lower() in ["high", "critical"]
            )
            db_session.add(db_pred)
            db_session.commit()
            db_session.refresh(db_pred)

            # Auto-create Review for high/critical findings
            if db_pred.requires_review:
                db_review = models.Review(
                    prediction_id=db_pred.id,
                    status="pending"
                )
                db_session.add(db_review)
                db_session.commit()

        scan.high_risk_count = high_count
        scan.critical_count = critical_count
        scan.status = "completed"
        scan.completed_at = get_utc_now()
        db_session.commit()

    except Exception as e:
        logger.error(f"Scan prediction processing failed: {str(e)}")
        scan.status = "failed"
        scan.completed_at = get_utc_now()
        db_session.commit()

@router.post("/api/v1/scans", response_model=schemas.ScanResponse, status_code=status.HTTP_201_CREATED)
async def trigger_scan(
    scan_in: schemas.ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    repo = db.query(models.Repository).filter(models.Repository.id == scan_in.repository_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    # Check ML Service health before proceeding
    if not await ml_client.is_healthy():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Service is unavailable, cannot process scan requests"
        )

    scan = models.Scan(
        repository_id=repo.id,
        requested_by=current_user.id,
        status="queued",
        commit_sha=scan_in.commit_sha or "runtime",
        total_changes=len(scan_in.changes),
        started_at=get_utc_now()
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Run predictions in BackgroundTasks (fast synchronous execution on main process)
    background_tasks.add_task(run_scan_prediction, scan.id, scan_in.changes, db)

    return scan

@router.get("/api/v1/scans", response_model=List[schemas.ScanResponse])
def list_scans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_viewer)
):
    return db.query(models.Scan).all()

@router.get("/api/v1/scans/{id}", response_model=schemas.ScanResponse)
def get_scan(
    id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_viewer)
):
    scan = db.query(models.Scan).filter(models.Scan.id == id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    return scan

@router.get("/api/v1/scans/{id}/predictions", response_model=List[schemas.PredictionResponseModel])
def get_scan_predictions(
    id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_viewer)
):
    scan = db.query(models.Scan).filter(models.Scan.id == id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    return db.query(models.Prediction).filter(models.Prediction.scan_id == id).all()
