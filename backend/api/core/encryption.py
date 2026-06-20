import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Load and validate FIELD_ENCRYPTION_KEY
key = os.environ.get("FIELD_ENCRYPTION_KEY")
if not key:
    raise RuntimeError("FIELD_ENCRYPTION_KEY environment variable is not set.")

try:
    # Fernet validates if it is a 32-byte urlsafe base64 key
    fernet_cipher = Fernet(key.encode('utf-8') if isinstance(key, str) else key)
except Exception as e:
    raise RuntimeError(f"FIELD_ENCRYPTION_KEY is not a valid 32-byte base64 Fernet key: {e}")

def encrypt_field(plaintext: str) -> str:
    """
    Encrypts the plaintext using Fernet symmetric encryption.
    """
    if not plaintext:
        return ""
    try:
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext_bytes = fernet_cipher.encrypt(plaintext_bytes)
        return ciphertext_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to encrypt field: {e}")
        raise e

def decrypt_field(ciphertext: str) -> str:
    """
    Decrypts the ciphertext using Fernet. If decryption fails, logs a warning and returns "[unable to decrypt]".
    
    NOTE: Existing unencrypted resume_text rows in the DB will fail decryption and will return "[unable to decrypt]".
    These legacy rows require a one-time migration/backfill script to be encrypted.
    """
    if not ciphertext:
        return ""
    try:
        ciphertext_bytes = ciphertext.encode('utf-8')
        plaintext_bytes = fernet_cipher.decrypt(ciphertext_bytes)
        return plaintext_bytes.decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to decrypt field (e.g. key rotated, corrupted data, or unencrypted legacy data): {e}")
        return "[unable to decrypt]"
