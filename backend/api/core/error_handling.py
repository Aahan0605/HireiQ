import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def safe_error_response(e: Exception, user_message: str, status_code: int = 500) -> HTTPException:
    """
    Logs the full error details with traceback server-side and returns
    a user-friendly, generic message to the client (preventing PII/internal leaks).
    """
    logger.error(f"{user_message}: {e}", exc_info=True)
    return HTTPException(status_code=status_code, detail=user_message)
