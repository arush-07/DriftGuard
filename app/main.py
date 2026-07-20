from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import httpx

from .config import settings
from .database import get_db, SessionLocal
from . import models
from .routers import auth, repositories, scans, reviews, dashboard

app = FastAPI(
    title="DriftGuard Backend API",
    version="1.0.0",
    description="Backend service for DriftGuard configuration-drift platform"
)

# Enable CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(repositories.router)
app.include_router(scans.router)
app.include_router(reviews.router)
app.include_router(dashboard.router)

@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        from .auth import get_password_hash
        
        # Seed default admin user
        admin = db.query(models.User).filter(models.User.email == "admin@driftguard.io").first()
        if not admin:
            admin = models.User(
                email="admin@driftguard.io",
                full_name="System Administrator",
                password_hash=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
            
        # Seed default viewer user
        viewer = db.query(models.User).filter(models.User.email == "viewer@driftguard.io").first()
        if not viewer:
            viewer = models.User(
                email="viewer@driftguard.io",
                full_name="System Viewer",
                password_hash=get_password_hash("viewer123"),
                role="viewer"
            )
            db.add(viewer)
            
        # Seed default repository
        repo = db.query(models.Repository).first()
        if not repo:
            repo = models.Repository(
                name="Synergy-2026/k8s-nginx-config-repo",
                provider="github",
                clone_url="https://github.com/Synergy-2026/k8s-nginx-config-repo.git",
                default_branch="main"
            )
            db.add(repo)
            
        db.commit()
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "driftguard-backend"
    }

@app.get("/ready")
async def ready(db: Session = Depends(get_db)):
    # Check database
    try:
        db.query(models.User).first()
    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {str(db_err)}"
        )

    # Check ML service
    ml_healthy = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.ML_SERVICE_URL}/health")
            if response.status_code == 200:
                ml_healthy = True
    except Exception as e:
        pass

    if not ml_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML service not ready"
        )

    return {
        "status": "ready",
        "database": "connected",
        "ml_service": "connected"
    }
