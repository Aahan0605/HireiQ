import os
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Retrieve key or generate dynamic fallback key
_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
if not _KEY:
    logger.warning("⚠️  FIELD_ENCRYPTION_KEY is missing! Using ephemeral key. Decryption will fail across server restarts.")
    _KEY = Fernet.generate_key().decode()

try:
    _cipher = Fernet(_KEY.encode())
except Exception as e:
    logger.error("Invalid FIELD_ENCRYPTION_KEY format. Generating dynamic fallback.")
    _KEY = Fernet.generate_key().decode()
    _cipher = Fernet(_KEY.encode())

def encrypt_field(val: str | None) -> str | None:
    """Encrypt PII field value to ciphertext."""
    if not val:
        return val
    try:
        return _cipher.encrypt(val.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error("Encryption failed: %s", e)
        return val

def decrypt_field(val: str | None) -> str | None:
    """Decrypt PII field ciphertext back to plaintext. Falls back to original value if invalid."""
    if not val:
        return val
    try:
        return _cipher.decrypt(val.encode('utf-8')).decode('utf-8')
    except Exception:
        # Graceful fallback: If it's not valid Fernet ciphertext, it's likely plaintext from old migrations
        return val
