from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current logged in user from JWT.
    If no token is supplied or token is invalid, raises 401 Unauthorized.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
        
    from db import get_supabase
    supabase = get_supabase()
    res = supabase.table("recruiters").select("*").eq("id", user_id).execute()
    user = res.data[0] if res.data else None
    if user is None:
        raise credentials_exception
        
    return user

async def get_optional_current_user(token: str = Depends(oauth2_scheme)) -> dict | None:
    """
    Get current logged in user from JWT if available, otherwise return None.
    Does not raise an exception.
    """
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    from db import get_supabase
    supabase = get_supabase()
    res = supabase.table("recruiters").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None
