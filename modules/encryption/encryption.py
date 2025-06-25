#!/usr/bin/env python3
import sys
import os
import time

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Import the sync module
from modules.sync.sync import CodeSync
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

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
            print_info(f"Loading existing master key from: {self.key_file}")
            self._load_keys()
            print_success("Master key loaded successfully")
        else:
            print_info(f"Generating new master key at: {self.key_file}")
            self._generate_keys()
            print_success("New master key generated successfully")

    def _generate_keys(self):
        """Generate new encryption keys."""
        # Check if keys already exist (double-check for safety)
        if self.key_file.exists():
            print_warning(f"Master key already exists at: {self.key_file}")
            print_warning("Loading existing keys instead of generating new ones")
            self._load_keys()
            return
        
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

        # Save keys with backup
        self._save_keys()

    def _save_keys(self):
        """Save encryption keys to file with backup protection."""
        # Create backup of existing keys if they exist
        if self.key_file.exists():
            backup_file = self.key_file.with_suffix('.key.backup')
            import shutil
            shutil.copy2(self.key_file, backup_file)
            print_warning(f"Existing master key backed up to: {backup_file}")
        
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
            'aes_key': base64.b64encode(self.aes_key).decode('utf-8'),
            'created_at': time.time(),
            'version': '1.0'
        }
        
        # Save to temporary file first, then move to final location
        temp_file = self.key_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(keys, f, indent=4)
        
        # Atomic move to final location
        temp_file.replace(self.key_file)
        print_success(f"Master key saved to: {self.key_file}")

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

    def backup_master_key(self, backup_path: str = None):
        """Create a backup of the master key."""
        if not self.key_file.exists():
            raise ValueError("No master key to backup")
        
        if backup_path is None:
            timestamp = int(time.time())
            backup_path = f"chain/keys/master.key.backup.{timestamp}"
        
        import shutil
        shutil.copy2(self.key_file, backup_path)
        print_success(f"Master key backed up to: {backup_path}")
        return backup_path

    def restore_master_key(self, backup_path: str):
        """Restore master key from backup."""
        if not os.path.exists(backup_path):
            raise ValueError(f"Backup file not found: {backup_path}")
        
        # Create backup of current key if it exists
        if self.key_file.exists():
            current_backup = f"{self.key_file}.current_backup"
            import shutil
            shutil.copy2(self.key_file, current_backup)
            print_warning(f"Current master key backed up to: {current_backup}")
        
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, self.key_file)
        print_success(f"Master key restored from: {backup_path}")
        
        # Reload keys
        self._load_keys()

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