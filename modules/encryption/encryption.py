#!/usr/bin/env python3
import sys
import os

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Import the sync module
from modules.sync.sync import CodeSync

def check_sync():
    """Check if code is synchronized with remote repository."""
    sync = CodeSync()
    if not sync.sync():
        print("Code synchronization failed. Please update your code.")
        sys.exit(1)

# Check code synchronization before proceeding
check_sync()

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import json
from typing import Tuple, Dict, Any, Optional
from pathlib import Path

class Encryption:
    def __init__(self, key_file: str = "chain/keys/master.key"):
        self.key_file = Path(key_file)
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones if they don't exist."""
        if self.key_file.exists():
            self._load_keys()
        else:
            self._generate_keys()

    def _generate_keys(self):
        """Generate new encryption keys."""
        # Generate Fernet key for symmetric encryption
        self.fernet_key = Fernet.generate_key()
        self.fernet = Fernet(self.fernet_key)

        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        # Generate AES key for private key encryption
        self.aes_key = os.urandom(32)  # 256-bit key

        # Save keys
        self._save_keys()

    def _save_keys(self):
        """Save encryption keys to file."""
        keys = {
            'fernet_key': base64.b64encode(self.fernet_key).decode('utf-8'),
            'private_key': self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8'),
            'public_key': self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8'),
            'aes_key': base64.b64encode(self.aes_key).decode('utf-8')
        }
        
        with open(self.key_file, 'w') as f:
            json.dump(keys, f, indent=4)

    def _load_keys(self):
        """Load encryption keys from file."""
        with open(self.key_file, 'r') as f:
            keys = json.load(f)
        
        self.fernet_key = base64.b64decode(keys['fernet_key'])
        self.fernet = Fernet(self.fernet_key)
        
        self.private_key = serialization.load_pem_private_key(
            keys['private_key'].encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        self.public_key = serialization.load_pem_public_key(
            keys['public_key'].encode('utf-8'),
            backend=default_backend()
        )
        
        self.aes_key = base64.b64decode(keys['aes_key'])

    def encrypt_private_key(self, private_key: str, passphrase: str) -> Dict[str, str]:
        """Encrypt a private key using AES-GCM with passphrase-derived key."""
        # Derive encryption key from passphrase
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(passphrase.encode('utf-8'))
        
        # Generate a random IV
        iv = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Add associated data (optional)
        encryptor.authenticate_additional_data(b"private_key")
        
        # Encrypt the private key
        ciphertext = encryptor.update(private_key.encode('utf-8')) + encryptor.finalize()
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8')
        }

    def decrypt_private_key(self, encrypted_data: Dict[str, str], passphrase: str) -> str:
        """Decrypt a private key using AES-GCM with passphrase-derived key."""
        # Decode the encrypted data
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        iv = base64.b64decode(encrypted_data['iv'])
        salt = base64.b64decode(encrypted_data['salt'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        # Derive the key using the same parameters
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(passphrase.encode('utf-8'))
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Add associated data (must match encryption)
        decryptor.authenticate_additional_data(b"private_key")
        
        # Decrypt the private key
        try:
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError("Failed to decrypt private key: Invalid passphrase or corrupted data")

    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using symmetric encryption (Fernet)."""
        return self.fernet.encrypt(data.encode('utf-8')).decode('utf-8')

    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption (Fernet)."""
        return self.fernet.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')

    def encrypt_asymmetric(self, data: str) -> str:
        """Encrypt data using asymmetric encryption (RSA)."""
        encrypted = self.public_key.encrypt(
            data.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using asymmetric encryption (RSA)."""
        encrypted = base64.b64decode(encrypted_data)
        decrypted = self.private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode('utf-8')

    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive an encryption key from a password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt

    def encrypt_with_password(self, data: str, password: str) -> Dict[str, str]:
        """Encrypt data using a password-derived key."""
        key, salt = self.derive_key_from_password(password)
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        encrypted = fernet.encrypt(data.encode('utf-8'))
        return {
            'encrypted_data': base64.b64encode(encrypted).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8')
        }

    def decrypt_with_password(self, encrypted_data: Dict[str, str], password: str) -> str:
        """Decrypt data using a password-derived key."""
        salt = base64.b64decode(encrypted_data['salt'])
        key, _ = self.derive_key_from_password(password, salt)
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        decrypted = fernet.decrypt(base64.b64decode(encrypted_data['encrypted_data']))
        return decrypted.decode('utf-8')

def main():
    # Example usage
    encryption = Encryption()
    
    # Test private key encryption
    private_key = "test_private_key_123"
    passphrase = "strong_passphrase_456"
    
    encrypted_key = encryption.encrypt_private_key(private_key, passphrase)
    decrypted_key = encryption.decrypt_private_key(encrypted_key, passphrase)
    print(f"Private key encryption test: {private_key == decrypted_key}")
    
    # Test symmetric encryption
    original_data = "Sensitive blockchain data"
    encrypted = encryption.encrypt_symmetric(original_data)
    decrypted = encryption.decrypt_symmetric(encrypted)
    print(f"Symmetric encryption test: {original_data == decrypted}")
    
    # Test asymmetric encryption
    encrypted = encryption.encrypt_asymmetric(original_data)
    decrypted = encryption.decrypt_asymmetric(encrypted)
    print(f"Asymmetric encryption test: {original_data == decrypted}")
    
    # Test password-based encryption
    password = "strong_password_123!"
    encrypted = encryption.encrypt_with_password(original_data, password)
    decrypted = encryption.decrypt_with_password(encrypted, password)
    print(f"Password-based encryption test: {original_data == decrypted}")

if __name__ == "__main__":
    main() 