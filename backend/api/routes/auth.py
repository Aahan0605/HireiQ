import uuid
import secrets
import os
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from api.core.security import verify_password, get_password_hash, create_access_token
from api.core.dependencies import get_current_user
from db.supabase_client import save_user, fetch_user_by_email
from db.session import SessionLocal
from db.models import User
from api.core.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "Recruiter"

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()

    from pydantic import validator
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    """Register a new user account."""
    existing_user = await fetch_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    hashed_password = get_password_hash(user_in.password)
    user_id = str(uuid.uuid4())
    
    user_data = {
        "id": user_id,
        "email": user_in.email,
        "hashed_password": hashed_password,
        "role": user_in.role
    }
    
    await save_user(user_data)
    
    # Generate verification token
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    # Save token to user record
    db = SessionLocal()
    try:
        user_record = db.query(User).filter(User.id == user_id).first()
        if user_record:
            user_record.verification_token = token
            user_record.verification_token_expires = expires
            user_record.is_verified = False
            db.commit()
    finally:
        db.close()
    
    # Send verification email (non-blocking)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    verification_link = f"{frontend_url}/verify-email?token={token}"
    
    asyncio.create_task(send_verification_email(user_in.email, verification_link))
    
    # Track user registration event in PostHog
    import posthog
    try:
        posthog.capture(
            distinct_id=user_id,
            event="user_signup",
            properties={
                "email": user_in.email,
                "role": user_in.role
            }
        )
    except Exception:
        pass
    
    return {
        "id": user_id,
        "email": user_in.email,
        "role": user_in.role,
        "message": "Registration successful. Please check your email to verify your account.",
        "email_verification_sent": True
    }

@router.post("/login", response_model=Token)
async def login_json(user_in: UserLogin):
    """Login with JSON payload (preferred for frontend integrations)."""
    user = await fetch_user_by_email(user_in.email)
    if not user or not verify_password(user_in.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in."
        )
    
    access_token = create_access_token(subject=user["id"])
    
    # Track user login event in PostHog
    import posthog
    try:
        posthog.capture(
            distinct_id=user["id"],
            event="user_login",
            properties={
                "email": user["email"],
                "role": user.get("role", "Recruiter")
            }
        )
    except Exception:
        pass

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user.get("role", "Recruiter")
        }
    }

@router.post("/login-oauth", response_model=dict)
async def login_oauth(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, for docs or general OAuth2 requests."""
    user = await fetch_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in."
        )
    
    access_token = create_access_token(subject=user["id"])
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/verify-email")
async def verify_email(token: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
        if user.verification_token_expires < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Verification token has expired. Please register again.")
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()
        return {"message": "Email verified successfully. You can now sign in."}
    finally:
        db.close()

@router.get("/me", response_model=dict)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Retrieve details of the currently authenticated user."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user.get("role", "Recruiter")
    }
