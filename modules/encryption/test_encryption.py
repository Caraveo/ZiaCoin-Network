import pytest
import os
from pathlib import Path
from .encryption import Encryption

@pytest.fixture
def encryption(tmp_path):
    """Create a temporary encryption instance for testing."""
    key_file = tmp_path / "test_keys.json"
    encryption = Encryption(str(key_file))
    yield encryption
    # Cleanup after tests
    if key_file.exists():
        os.remove(key_file)

def test_key_generation_and_loading(encryption):
    """Test that keys are generated and loaded correctly."""
    # Verify keys exist
    assert encryption.fernet_key is not None
    assert encryption.private_key is not None
    assert encryption.public_key is not None
    
    # Create new instance to test loading
    new_encryption = Encryption(str(encryption.key_file))
    assert new_encryption.fernet_key == encryption.fernet_key
    assert new_encryption.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ) == encryption.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def test_symmetric_encryption(encryption):
    """Test symmetric encryption and decryption."""
    original_data = "Test data for symmetric encryption"
    
    # Encrypt
    encrypted = encryption.encrypt_symmetric(original_data)
    assert encrypted != original_data
    
    # Decrypt
    decrypted = encryption.decrypt_symmetric(encrypted)
    assert decrypted == original_data

def test_asymmetric_encryption(encryption):
    """Test asymmetric encryption and decryption."""
    original_data = "Test data for asymmetric encryption"
    
    # Encrypt
    encrypted = encryption.encrypt_asymmetric(original_data)
    assert encrypted != original_data
    
    # Decrypt
    decrypted = encryption.decrypt_asymmetric(encrypted)
    assert decrypted == original_data

def test_password_based_encryption(encryption):
    """Test password-based encryption and decryption."""
    original_data = "Test data for password-based encryption"
    password = "test_password_123!"
    
    # Encrypt
    encrypted = encryption.encrypt_with_password(original_data, password)
    assert 'encrypted_data' in encrypted
    assert 'salt' in encrypted
    assert encrypted['encrypted_data'] != original_data
    
    # Decrypt
    decrypted = encryption.decrypt_with_password(encrypted, password)
    assert decrypted == original_data

def test_password_based_encryption_wrong_password(encryption):
    """Test that wrong password fails to decrypt."""
    original_data = "Test data"
    password = "correct_password"
    wrong_password = "wrong_password"
    
    encrypted = encryption.encrypt_with_password(original_data, password)
    
    with pytest.raises(Exception):
        encryption.decrypt_with_password(encrypted, wrong_password)

def test_large_data_encryption(encryption):
    """Test encryption of larger data."""
    original_data = "x" * 1000  # 1000 bytes of data
    
    # Test symmetric
    encrypted = encryption.encrypt_symmetric(original_data)
    decrypted = encryption.decrypt_symmetric(encrypted)
    assert decrypted == original_data
    
    # Test asymmetric
    encrypted = encryption.encrypt_asymmetric(original_data)
    decrypted = encryption.decrypt_asymmetric(encrypted)
    assert decrypted == original_data
    
    # Test password-based
    password = "test_password"
    encrypted = encryption.encrypt_with_password(original_data, password)
    decrypted = encryption.decrypt_with_password(encrypted, password)
    assert decrypted == original_data

def test_special_characters(encryption):
    """Test encryption with special characters."""
    original_data = "!@#$%^&*()_+{}|:<>?[]\\;',./~`"
    
    # Test symmetric
    encrypted = encryption.encrypt_symmetric(original_data)
    decrypted = encryption.decrypt_symmetric(encrypted)
    assert decrypted == original_data
    
    # Test asymmetric
    encrypted = encryption.encrypt_asymmetric(original_data)
    decrypted = encryption.decrypt_asymmetric(encrypted)
    assert decrypted == original_data
    
    # Test password-based
    password = "!@#$%^&*()"
    encrypted = encryption.encrypt_with_password(original_data, password)
    decrypted = encryption.decrypt_with_password(encrypted, password)
    assert decrypted == original_data

if __name__ == "__main__":
    pytest.main(['-v', 'test_encryption.py']) 