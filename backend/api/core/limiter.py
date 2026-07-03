import os
import uuid
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _bypass_requested(request: Request) -> bool:
    """
    Returns True only when a rate-limit bypass key is explicitly configured via
    the environment AND the incoming request presents the matching header.

    The bypass has no default value: if BYPASS_RATE_LIMIT_KEY is unset or blank
    (the production default), no header can ever bypass rate limiting. This
    prevents an external client from disabling brute-force protection with a
    guessable/hardcoded key.
    """
    bypass_key = (os.getenv("BYPASS_RATE_LIMIT_KEY") or "").strip()
    if not bypass_key:
        return False
    return request.headers.get("X-Bypass-Rate-Limit") == bypass_key


def get_remote_address_with_bypass(request: Request) -> str:
    """Gets the remote address, or returns a unique UUID if bypass is configured and requested."""
    if _bypass_requested(request):
        return str(uuid.uuid4())
    return get_remote_address(request)

def get_user_or_ip(request: Request) -> str:
    """
    Rate limiting key function.
    Returns 'user:{user_id}' if the user is authenticated via Bearer token,
    otherwise falls back to remote IP address.
    Supports rate limit bypass only when explicitly configured via env.
    """
    if _bypass_requested(request):
        return str(uuid.uuid4())

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
    key_func=get_remote_address_with_bypass,
    default_limits=["100/minute"],
    enabled=not is_testing
)
