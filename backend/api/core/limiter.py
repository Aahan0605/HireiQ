import os
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_user_or_ip(request: Request) -> str:
    """
    Rate limiting key function.
    Returns 'user:{user_id}' if the user is authenticated via Bearer token,
    otherwise falls back to remote IP address.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from api.core.security import decode_access_token
            user_id = decode_access_token(token)
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)

# Define global rate limiter with default 100 requests per minute per IP
is_testing = os.getenv("TESTING") == "true" or os.getenv("PYTEST_CURRENT_TEST") is not None

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    enabled=not is_testing
)
