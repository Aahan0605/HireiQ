import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from api.core.security import verify_password, get_password_hash, create_access_token
from api.core.dependencies import get_current_user
from db.supabase_client import save_user, fetch_user_by_email

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
    
    # Return user details without password hash
    return {
        "id": user_id,
        "email": user_in.email,
        "role": user_in.role,
        "message": "User registered successfully."
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
    
    access_token = create_access_token(subject=user["id"])
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=dict)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Retrieve details of the currently authenticated user."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user.get("role", "Recruiter")
    }
