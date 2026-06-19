import uuid
import secrets
import os
import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from api.core.security import verify_password, get_password_hash, create_access_token
from api.core.dependencies import get_current_user
from db import get_supabase
from api.core.email import send_verification_email, send_password_reset_email
from api.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "Owner"
    company: str = ""
    full_name: str = ""

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()

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

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isalpha() for c in v):
            raise ValueError('Must contain a letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Must contain a digit')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

async def fetch_user_by_email(email: str) -> dict | None:
    try:
        supabase = get_supabase()
        res = supabase.table("recruiters").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        raise e

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    """Register a new recruiter account."""
    try:
        existing_user = await fetch_user_by_email(user_in.email)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}. Please check your backend/.env database configuration."
        )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    hashed_password = get_password_hash(user_in.password)
    user_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    try:
        supabase = get_supabase()
        supabase.table("recruiters").insert({
            "id": user_id,
            "email": user_in.email,
            "hashed_password": hashed_password,
            "role": user_in.role,
            "company": user_in.company,
            "full_name": user_in.full_name,
            "verification_token": token,
            "verification_token_expires": expires.isoformat(),
            "is_verified": not bool(os.getenv("RESEND_API_KEY")),
            "plan": "free"
        }).execute()
        
        # Initialize default weights for this recruiter
        supabase.table("scoring_weights").insert({
            "recruiter_id": user_id,
            "skills_weight": 0.4,
            "experience_weight": 0.3,
            "education_weight": 0.2,
            "github_weight": 0.1
        }).execute()
    except Exception as e:
        logger.error(f"Database error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error during registration: {str(e)}. Please check your backend/.env database configuration."
        )
    
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
@limiter.limit("10/15minute")
async def login_json(request: Request, user_in: UserLogin):
    """Login with JSON payload."""
    try:
        user = await fetch_user_by_email(user_in.email)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}. Please check your SUPABASE_URL and credentials in backend/.env."
        )
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
                "role": user.get("role", "Owner")
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
            "role": user.get("role", "Owner")
        }
    }

@router.post("/login-oauth", response_model=dict)
async def login_oauth(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login."""
    try:
        user = await fetch_user_by_email(form_data.username)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}. Please check your SUPABASE_URL and credentials in backend/.env."
        )
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
    try:
        supabase = get_supabase()
        res = supabase.table("recruiters").select("*").eq("verification_token", token).execute()
        user = res.data[0] if res.data else None
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
        
        expires_str = user.get("verification_token_expires")
        if expires_str:
            expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            now = datetime.now(expires.tzinfo) if expires.tzinfo else datetime.utcnow()
            if expires < now:
                raise HTTPException(status_code=400, detail="Verification token has expired. Please register again.")
        
        supabase.table("recruiters").update({
            "is_verified": True,
            "verification_token": None,
            "verification_token_expires": None
        }).eq("id", user["id"]).execute()
        
        return {"message": "Email verified successfully. You can now sign in."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during verification.")

@router.get("/me", response_model=dict)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Retrieve details of the currently authenticated user."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user.get("role", "Owner")
    }

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Always return 200 to prevent email enumeration."""
    try:
        user = await fetch_user_by_email(req.email)
        if user:
            token = secrets.token_urlsafe(32)
            expires = datetime.utcnow() + timedelta(hours=1)
            supabase = get_supabase()
            supabase.table("recruiters").update({
                "password_reset_token": token,
                "password_reset_expires": expires.isoformat()
            }).eq("id", user["id"]).execute()
            
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
            reset_link = f"{frontend_url}/reset-password?token={token}"
            asyncio.create_task(send_password_reset_email(req.email, reset_link))
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}")
    return {"message": "If that email exists, a reset link has been sent."}

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    try:
        supabase = get_supabase()
        res = supabase.table("recruiters").select("*").eq("password_reset_token", req.token).execute()
        user = res.data[0] if res.data else None
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
        
        expires_str = user.get("password_reset_expires")
        if expires_str:
            expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            now = datetime.now(expires.tzinfo) if expires.tzinfo else datetime.utcnow()
            if expires < now:
                raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
                
        supabase.table("recruiters").update({
            "hashed_password": get_password_hash(req.new_password),
            "password_reset_token": None,
            "password_reset_expires": None
        }).eq("id", user["id"]).execute()
        
        return {"message": "Password reset successfully. You can now sign in."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail="An error occurred resetting password.")
