from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()

@router.get("/api/v1/reviews", response_model=List[schemas.ReviewResponse])
def list_reviews(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_viewer)
):
    return db.query(models.Review).all()

@router.patch("/api/v1/reviews/{id}", response_model=schemas.ReviewResponse)
def update_review(
    id: str,
    review_update: schemas.ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    review = db.query(models.Review).filter(models.Review.id == id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Decisions allowed: resolved | dismissed
    if review_update.decision not in ["resolved", "dismissed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be resolved or dismissed"
        )

    review.status = review_update.decision
    review.decision = review_update.decision
    review.notes = review_update.notes
    review.reviewer_id = current_user.id
    review.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(review)
    return review
