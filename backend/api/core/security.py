import os
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
import bcrypt
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT configuration
# IMPORTANT: In production, always set JWT_SECRET_KEY in .env
_default_secret = secrets.token_hex(32)  # Random per-process fallback
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip() or _default_secret

if os.getenv("JWT_SECRET_KEY", "").strip() == "":
    import logging
    logging.getLogger(__name__).warning(
        "⚠️  JWT_SECRET_KEY is not set! Using a random per-process secret. "
        "Tokens will NOT survive server restarts. Set JWT_SECRET_KEY in your .env file."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash of a password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for a subject (usually user ID or email)."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[str]:
    """Decode a JWT access token and return the subject."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
