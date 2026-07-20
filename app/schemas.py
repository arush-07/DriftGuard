from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "viewer"  # admin | viewer

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

# --- Repository Schemas ---
class RepositoryCreate(BaseModel):
    name: str
    provider: Optional[str] = "manual"
    clone_url: Optional[str] = None
    default_branch: Optional[str] = "main"

class RepositoryResponse(BaseModel):
    id: str
    name: str
    provider: str
    clone_url: Optional[str]
    default_branch: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Scan & Prediction Schemas ---
class ConfigurationChangeInput(BaseModel):
    file_path: str
    configuration_type: str
    field_path: str
    old_value: str
    new_value: str
    commit_message: Optional[str] = ""
    commit_hash: Optional[str] = ""

class ScanCreate(BaseModel):
    repository_id: str
    commit_sha: Optional[str] = None
    changes: List[ConfigurationChangeInput]

class ChangeRecordResponse(BaseModel):
    id: str
    scan_id: str
    file_path: str
    configuration_type: str
    field_path: str
    old_value_redacted: Optional[str]
    new_value_redacted: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PredictionResponseModel(BaseModel):
    id: str
    scan_id: str
    change_id: str
    predicted_class: str
    risk_level: str
    confidence: float
    drift_score: float
    rule_flags: Optional[Dict[str, Any]]
    raw_response: Optional[Dict[str, Any]]
    model_version: Optional[str]
    requires_review: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ScanResponse(BaseModel):
    id: str
    repository_id: str
    requested_by: Optional[str]
    status: str
    commit_sha: Optional[str]
    total_changes: int
    high_risk_count: int
    critical_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Review Schemas ---
class ReviewUpdate(BaseModel):
    decision: str  # resolved | dismissed
    notes: Optional[str] = None

class ReviewResponse(BaseModel):
    id: str
    prediction_id: str
    reviewer_id: Optional[str]
    status: str
    decision: Optional[str]
    notes: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True
