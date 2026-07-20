import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer", nullable=False) # admin | viewer
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), default="manual", nullable=False) # github | manual
    clone_url = Column(String(500), nullable=True)
    default_branch = Column(String(100), default="main", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    scans = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="queued", nullable=False) # queued | processing | completed | failed
    commit_sha = Column(String(100), nullable=True)
    total_changes = Column(Integer, default=0, nullable=False)
    high_risk_count = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    repository = relationship("Repository", back_populates="scans")
    changes = relationship("ChangeRecord", back_populates="scan", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="scan", cascade="all, delete-orphan")


class ChangeRecord(Base):
    __tablename__ = "change_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    configuration_type = Column(String(50), nullable=False)
    field_path = Column(String(500), nullable=False)
    old_value_redacted = Column(String(2000), nullable=True)
    new_value_redacted = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    scan = relationship("Scan", back_populates="changes")
    predictions = relationship("Prediction", back_populates="change", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    change_id = Column(String(36), ForeignKey("change_records.id"), nullable=False)
    predicted_class = Column(String(100), nullable=False)
    risk_level = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    drift_score = Column(Float, default=0.0, nullable=False)
    rule_flags = Column(JSON, nullable=True)
    raw_response = Column(JSON, nullable=True)
    model_version = Column(String(100), nullable=True)
    requires_review = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    scan = relationship("Scan", back_populates="predictions")
    change = relationship("ChangeRecord", back_populates="predictions")
    reviews = relationship("Review", back_populates="prediction", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prediction_id = Column(String(36), ForeignKey("predictions.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="pending", nullable=False) # pending | resolved | dismissed
    decision = Column(String(100), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    prediction = relationship("Prediction", back_populates="reviews")
