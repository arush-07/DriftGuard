from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()

@router.post("/api/v1/repositories", response_model=schemas.RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    repo_in: schemas.RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    repo = models.Repository(
        name=repo_in.name,
        provider=repo_in.provider,
        clone_url=repo_in.clone_url,
        default_branch=repo_in.default_branch
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo

@router.get("/api/v1/repositories", response_model=List[schemas.RepositoryResponse])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_viewer)
):
    return db.query(models.Repository).all()

@router.get("/api/v1/repositories/{id}", response_model=schemas.RepositoryResponse)
def get_repository(
    id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_viewer)
):
    repo = db.query(models.Repository).filter(models.Repository.id == id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    return repo
