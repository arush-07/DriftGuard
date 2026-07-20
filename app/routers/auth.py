from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()

def register_user_logic(user_in: schemas.UserRegister, db: Session):
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Restrict roles to admin/viewer
    role = user_in.role
    if role not in ["admin", "viewer"]:
        role = "viewer"

    hashed_pw = auth.get_password_hash(user_in.password)
    user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hashed_pw,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def login_user_logic(credentials: schemas.UserLogin, db: Session):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

# Official API schemas
@router.post("/api/v1/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    return register_user_logic(user_in, db)

@router.post("/api/v1/auth/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    return login_user_logic(credentials, db)

@router.get("/api/v1/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# Frontend API compatibility
@router.post("/auth/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    return register_user_logic(user_in, db)

@router.post("/auth/login", response_model=schemas.TokenResponse)
def frontend_login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    return login_user_logic(credentials, db)
