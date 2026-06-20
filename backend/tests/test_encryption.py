import pytest
from api.core.encryption import encrypt_field, decrypt_field

def test_encryption_decryption_cycle():
    original = "Hello World! This is some sensitive resume PII."
    encrypted = encrypt_field(original)
    
    assert encrypted != original
    assert len(encrypted) > 0
    
    decrypted = decrypt_field(encrypted)
    assert decrypted == original

def test_encryption_empty():
    assert encrypt_field("") == ""
    assert decrypt_field("") == ""
    assert encrypt_field(None) == ""
    assert decrypt_field(None) == ""

def test_decryption_failure():
    # Invalid ciphertext should return the placeholder and log a warning
    assert decrypt_field("invalid-ciphertext") == "[unable to decrypt]"
    assert decrypt_field("gAAAAABmRandomGarbageHere") == "[unable to decrypt]"
